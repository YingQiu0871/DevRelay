<#
DevRelay v0.3-E G0.4 rerun harness (revision 4 composite).
Definition: V03E_G0_4_API_INSPECTION_ORACLE.md (revision 3) + V03E_G0_4_RERUN_PROVISIONING_ADDENDUM.md.
Run exactly once, only after the owner's authorization is recorded.  It never retries,
never tries another port/address/server, issues at most one loopback GET /doc and no
other HTTP.  Evidence is written outside git to -EvidenceDir.  PowerShell 7+.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $EvidenceDir,
    [Parameter(Mandatory)] [string] $WorkspaceRoot,
    [Parameter(Mandatory)] [string] $RepoRoot,
    [Parameter(Mandatory)] [int] $Port,
    [Parameter(Mandatory)] [string] $AuthorizedAtUtc,
    [string] $Python = "python"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
# Native exit codes are checked explicitly; a host profile must not turn them into exceptions.
$PSNativeCommandUseErrorActionPreference = $false

$ExpectedSha = "578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35"
$ExpectedSize = 174182280
$MaxBody = 64MB
$PackageRoot = Join-Path $env:APPDATA "npm\node_modules\opencode-ai"
$DefinitionFiles = @(
    "docs/v0.3/V03E_G0_4_API_INSPECTION_ORACLE.md",
    "docs/v0.3/V03E_G0_4_RERUN_PROVISIONING_ADDENDUM.md",
    "docs/v0.3/V03E_G0_4_RERUN_HARNESS.ps1"
)

# ---- PREFLIGHT (not a proof action; refusal consumes nothing) -------------
if (Test-Path $EvidenceDir) { throw "PREFLIGHT_REFUSED: evidence directory already exists; a round runs once" }
if ($AuthorizedAtUtc -notmatch 'Z$') { throw "PREFLIGHT_REFUSED: -AuthorizedAtUtc must be ISO-8601 UTC ending in Z" }
$AuthorizedAt = [datetime]::Parse($AuthorizedAtUtc, [Globalization.CultureInfo]::InvariantCulture,
    [Globalization.DateTimeStyles]::RoundtripKind)
if ($AuthorizedAt.Kind -ne [DateTimeKind]::Utc) { throw "PREFLIGHT_REFUSED: authorization time is not UTC" }
if ($Port -lt 1024 -or $Port -gt 65535 -or $Port -eq 45278) { throw "PREFLIGHT_REFUSED: port not allowed" }
$head = (& git -C $RepoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw "PREFLIGHT_REFUSED: repository HEAD unreadable" }
$dirty = @(& git -C $RepoRoot status --porcelain)
if ($dirty.Count -ne 0) { throw "PREFLIGHT_REFUSED: repository tree is not clean" }
$definition = [ordered]@{}
foreach ($f in $DefinitionFiles) {
    $blob = (& git -C $RepoRoot rev-parse "HEAD:$f").Trim()
    if ($LASTEXITCODE -ne 0) { throw "PREFLIGHT_REFUSED: $f is not committed" }
    $tmp = [IO.Path]::GetTempFileName()
    try {
        & cmd /c "git -C `"$RepoRoot`" cat-file blob $blob > `"$tmp`""
        $definition[$f] = [ordered]@{ blob = $blob; sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $tmp).Hash.ToLowerInvariant() }
    } finally { Remove-Item -LiteralPath $tmp -Force }
}
New-Item -ItemType Directory -Path $EvidenceDir | Out-Null

$Counters = [ordered]@{
    provisioning_opencode_starts = 0; proof_opencode_starts = 0; loopback_get_count = 0
    other_http_count = 0; provider_model_calls = 0; harness_external_connections = 0
}
$State = [ordered]@{
    reason = $null; target_bound = $false; continuity = $null; b1 = $null
    final_verdict = $null; awaiting = $null
}
$Started = $null
$Observed = [System.Collections.Generic.List[string]]::new()

function Save($name, $obj) {
    $obj | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 (Join-Path $EvidenceDir $name)
}
function Fail($reason) { if (-not $State.reason) { $State.reason = $reason } }
function Canon($path) { [IO.Path]::GetFullPath((Get-Item -LiteralPath $path).FullName).ToLowerInvariant() }
function FileId($path) {
    $o = & fsutil file queryfileid $path 2>&1
    if ($LASTEXITCODE -eq 0) { return [ordered]@{ value = ($o -join " ").Trim(); note = "" } }
    return [ordered]@{ value = "unavailable"; note = (($o -join " ").Trim()) }
}
function FileFacts($path) {
    $item = Get-Item -LiteralPath $path
    $id = FileId $path
    [ordered]@{
        path = Canon $path; sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
        size = $item.Length; last_write_utc = $item.LastWriteTimeUtc.ToString("o")
        file_id = $id.value; file_id_note = $id.note
        reparse = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
    }
}
function Listeners() {
    @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { [pscustomobject]@{ address = $_.LocalAddress; pid = [int]$_.OwningProcess } })
}
function ProcessTree([int] $root) {
    $all = @(Get-CimInstance Win32_Process)
    $ids = [System.Collections.Generic.List[int]]::new(); $ids.Add($root)
    for ($i = 0; $i -lt $ids.Count; $i++) {
        foreach ($c in $all) { if ([int]$c.ParentProcessId -eq $ids[$i] -and -not $ids.Contains([int]$c.ProcessId)) { $ids.Add([int]$c.ProcessId) } }
    }
    return ,$ids.ToArray()
}
function SampleExternal([int] $root) {
    foreach ($id in (ProcessTree $root)) {
        foreach ($c in @(Get-NetTCPConnection -OwningProcess $id -ErrorAction SilentlyContinue)) {
            if ($c.State -ne "Listen" -and $c.RemoteAddress -notin @("127.0.0.1", "::1", "0.0.0.0", "::")) {
                $Observed.Add("pid $id -> $($c.RemoteAddress):$($c.RemotePort) $($c.State)")
            }
        }
    }
}
function Snapshot($label) {
    $ls = @(Listeners)
    $snap = [ordered]@{ label = $label; taken_utc = (Get-Date).ToUniversalTime().ToString("o"); listeners = $ls; process = $null; executable = $null }
    $snap.listener_unambiguous = ($ls.Count -eq 1 -and $ls[0].address -eq "127.0.0.1")
    if (-not $snap.listener_unambiguous) { return $snap }
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $($ls[0].pid)"
    if (-not $proc -or -not $proc.ExecutablePath -or -not $proc.CreationDate) { return $snap }
    $snap.process = [ordered]@{
        pid = [int]$proc.ProcessId; parent_pid = [int]$proc.ParentProcessId
        creation_utc = $proc.CreationDate.ToUniversalTime().ToString("o")
        command_line_redacted = ("$($proc.CommandLine)" -replace [regex]::Escape($env:USERPROFILE), "%USERPROFILE%")
    }
    $snap.executable = FileFacts $proc.ExecutablePath
    return $snap
}
function SameTarget($a, $b) {
    return ($a.process.pid -eq $b.process.pid -and $a.process.creation_utc -eq $b.process.creation_utc -and
        $a.executable.path -eq $b.executable.path -and $a.executable.sha256 -eq $b.executable.sha256 -and
        $a.executable.size -eq $b.executable.size -and $a.executable.last_write_utc -eq $b.executable.last_write_utc -and
        $a.executable.file_id -eq $b.executable.file_id)
}
function IndexOfCrlfCrlf([byte[]] $buf, [int] $len) {
    for ($i = 0; $i -le $len - 4; $i++) {
        if ($buf[$i] -eq 13 -and $buf[$i+1] -eq 10 -and $buf[$i+2] -eq 13 -and $buf[$i+3] -eq 10) { return $i }
    }
    return -1
}
# Returns @{ ok; body; error } — malformed framing is a semantic B1 failure, never an exception.
function Dechunk([byte[]] $data) {
    $out = [IO.MemoryStream]::new(); $pos = 0
    while ($true) {
        $lineEnd = $pos
        while ($lineEnd -lt $data.Length - 1 -and -not ($data[$lineEnd] -eq 13 -and $data[$lineEnd+1] -eq 10)) { $lineEnd++ }
        if ($lineEnd -ge $data.Length - 1) { return @{ ok = $false; body = $null; error = "CHUNK_TRUNCATED" } }
        $hex = ([Text.Encoding]::ASCII.GetString($data, $pos, $lineEnd - $pos) -split ";")[0].Trim()
        $size = 0
        if (-not [int]::TryParse($hex, [Globalization.NumberStyles]::HexNumber, $null, [ref]$size) -or $size -lt 0) {
            return @{ ok = $false; body = $null; error = "CHUNK_SIZE_MALFORMED" }
        }
        if ($size -eq 0) { return @{ ok = $true; body = $out.ToArray(); error = $null } }
        $start = $lineEnd + 2
        if ($start + $size + 2 -gt $data.Length) { return @{ ok = $false; body = $null; error = "CHUNK_TRUNCATED" } }
        $out.Write($data, $start, $size); $pos = $start + $size + 2
    }
}

try {
    Save "preflight.json" ([ordered]@{
        repository_head = $head; tree_clean = $true; definition = $definition
        powershell = "$($PSVersionTable.PSVersion)"; os = "$($PSVersionTable.OS)"
        harness_pid = $PID; authorized_at_utc = $AuthorizedAt.ToString("o"); port = $Port
        workspace_root = $WorkspaceRoot
    })

    # ---- STEP 1: target statics (before any start) -----------------------
    $pkg = Get-Content -Raw (Join-Path $PackageRoot "package.json") | ConvertFrom-Json
    $binRel = if ($pkg.bin -is [string]) { $pkg.bin } else { "$($pkg.bin.opencode)" }
    $declared = Join-Path $PackageRoot $binRel
    $statics = [ordered]@{ package_root = Canon $PackageRoot; name = $pkg.name; version = $pkg.version; declared_bin = $binRel }
    $statics.target = FileFacts $declared
    Save "statics.json" $statics
    if ($pkg.name -ne "opencode-ai" -or $pkg.version -ne "1.18.11" -or $binRel -ne "./bin/opencode.exe" -or
        $statics.target.sha256 -ne $ExpectedSha -or $statics.target.size -ne $ExpectedSize -or $statics.target.reparse) {
        Fail "TARGET_INSTANCE_MISMATCH"; throw "stop"
    }

    # ---- STEP 2: configured endpoint (accepted runtime wiring loader) ----
    $env:PYTHONPATH = Join-Path $RepoRoot "src"
    $lines = @(& $Python -c "import sys; from devrelay.config import load_wiring_config; print(load_wiring_config(sys.argv[1]).opencode.base_url)" $WorkspaceRoot)
    $pyExit = $LASTEXITCODE
    $expected = "http://127.0.0.1:$Port"
    $endpoint = if ($pyExit -eq 0 -and $lines.Count -eq 1) { "$($lines[0])".Trim() } else { $null }
    Save "config.json" ([ordered]@{ workspace_root = $WorkspaceRoot; loader = "load_wiring_config"; exit_code = $pyExit
        output_lines = $lines.Count; configured_endpoint = $endpoint; required = $expected })
    if ($endpoint -ne $expected) { Fail "ENDPOINT_NOT_LITERAL_LOOPBACK"; throw "stop" }

    # ---- PROVISION: exactly one start ------------------------------------
    if (@(Listeners).Count -ne 0) { Save "provisioning.json" ([ordered]@{ port_busy = Listeners }); Fail "PROVISION_PORT_BUSY"; throw "stop" }
    $ocHome = Join-Path $EvidenceDir "opencode-home"
    $dirs = [ordered]@{
        XDG_CONFIG_HOME = Join-Path $ocHome "config"; XDG_DATA_HOME = Join-Path $ocHome "data"
        XDG_CACHE_HOME = Join-Path $ocHome "cache"; XDG_STATE_HOME = Join-Path $ocHome "state"
    }
    foreach ($d in $dirs.Values) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
    $removed = @("OPENCODE_SERVER_PASSWORD", "OPENCODE_SERVER_USERNAME", "OPENCODE_CONFIG", "OPENCODE_CONFIG_CONTENT",
        "OPENCODE_CONFIG_DIR", "OPENCODE_API_KEY", "OPENCODE_AUTH_CONTENT")
    $flags = @("OPENCODE_DISABLE_AUTOUPDATE", "OPENCODE_DISABLE_MODELS_FETCH", "OPENCODE_DISABLE_DEFAULT_PLUGINS",
        "OPENCODE_DISABLE_LSP_DOWNLOAD", "OPENCODE_DISABLE_SHARE", "OPENCODE_DISABLE_EXTERNAL_SKILLS",
        "OPENCODE_DISABLE_CLAUDE_CODE", "OPENCODE_DISABLE_PROJECT_CONFIG")
    $saved = @{}
    foreach ($n in $removed + $flags + @($dirs.Keys)) { $saved[$n] = [Environment]::GetEnvironmentVariable($n, "Process") }
    foreach ($n in $removed) { [Environment]::SetEnvironmentVariable($n, $null, "Process") }
    foreach ($n in $flags) { [Environment]::SetEnvironmentVariable($n, "1", "Process") }
    foreach ($k in $dirs.Keys) { [Environment]::SetEnvironmentVariable($k, $dirs[$k], "Process") }
    $startUtc = (Get-Date).ToUniversalTime()
    try {
        $Counters.provisioning_opencode_starts = 1
        $Started = Start-Process -FilePath $declared -ArgumentList @("serve", "--hostname", "127.0.0.1", "--port", "$Port") `
            -WorkingDirectory $WorkspaceRoot -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $EvidenceDir "server-stdout.log") `
            -RedirectStandardError (Join-Path $EvidenceDir "server-stderr.log")
    } finally {
        foreach ($n in $saved.Keys) { [Environment]::SetEnvironmentVariable($n, $saved[$n], "Process") }
    }
    $deadline = (Get-Date).AddSeconds(60)
    while (@(Listeners).Count -eq 0 -and (Get-Date) -lt $deadline -and -not $Started.HasExited) { Start-Sleep -Milliseconds 250 }
    Save "provisioning.json" ([ordered]@{
        harness_pid = $PID; started_pid = $Started.Id; started_utc = $startUtc.ToString("o")
        command = "<declared-bin> serve --hostname 127.0.0.1 --port $Port"; working_directory = $WorkspaceRoot
        env_removed = $removed; env_set_1 = $flags; xdg = $dirs; exited_early = $Started.HasExited
        listener_ready = (@(Listeners).Count -gt 0)
    })
    if (@(Listeners).Count -eq 0) { Fail "PROVISION_NO_LISTENER"; throw "stop" }

    # ---- STEP 3: pre-snapshot + TARGET_BOUND -----------------------------
    $pre = Snapshot "pre"
    Save "pre.json" $pre
    SampleExternal $Started.Id
    if (-not $pre.listener_unambiguous) { Fail "TARGET_IDENTITY_AMBIGUOUS"; throw "stop" }
    if (-not $pre.process) { Fail "TARGET_IDENTITY_UNRESOLVED"; throw "stop" }
    $x = $pre.executable
    if ($x.path -ne $statics.target.path -or $x.sha256 -ne $statics.target.sha256 -or $x.size -ne $statics.target.size -or
        $x.file_id -ne $statics.target.file_id) { Fail "TARGET_INSTANCE_MISMATCH"; throw "stop" }
    $created = [datetime]::Parse($pre.process.creation_utc, [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
    $written = [datetime]::Parse($x.last_write_utc, [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
    if ($pre.process.pid -ne $Started.Id -or $pre.process.parent_pid -ne $PID -or $created -lt $AuthorizedAt -or $written -gt $created) {
        Fail "TARGET_IDENTITY_UNRESOLVED"; throw "stop"
    }
    $State.target_bound = $true

    # ---- STEP 4: exactly one GET /doc (failures are semantic) ------------
    $get = [ordered]@{ outcome = $null; local_endpoint = $null; remote_endpoint = $null; status_code = $null
        status_line = $null; content_type = $null; content_length = $null; chunked = $false
        body_bytes = 0; body_sha256 = $null }
    $body = $null
    $Counters.loopback_get_count = 1
    try {
        $client = [Net.Sockets.TcpClient]::new([Net.Sockets.AddressFamily]::InterNetwork)
        try {
            $client.ReceiveTimeout = 30000; $client.SendTimeout = 30000
            $client.Connect([Net.IPAddress]::Parse("127.0.0.1"), $Port)
            $get.local_endpoint = "$($client.Client.LocalEndPoint)"; $get.remote_endpoint = "$($client.Client.RemoteEndPoint)"
            $stream = $client.GetStream()
            $req = [Text.Encoding]::ASCII.GetBytes("GET /doc HTTP/1.1`r`nHost: 127.0.0.1:$Port`r`nAccept: application/json`r`nConnection: close`r`n`r`n")
            $stream.Write($req, 0, $req.Length)
            $ms = [IO.MemoryStream]::new(); $buf = [byte[]]::new(65536); $hdrEnd = -1; $done = $false
            while (-not $done) {
                $n = $stream.Read($buf, 0, $buf.Length)
                if ($n -le 0) { break }
                $ms.Write($buf, 0, $n)
                if ($ms.Length -gt $MaxBody) { $get.outcome = "BODY_TOO_LARGE"; break }
                $all = $ms.ToArray()
                if ($hdrEnd -lt 0) {
                    $hdrEnd = IndexOfCrlfCrlf $all $all.Length
                    if ($hdrEnd -ge 0) {
                        $headText = [Text.Encoding]::ASCII.GetString($all, 0, $hdrEnd)
                        $get.status_line = ($headText -split "`r`n")[0]
                        if ($get.status_line -match '^HTTP/\d\.\d (\d{3})') { $get.status_code = [int]$Matches[1] }
                        if ($headText -match '(?im)^content-type:\s*(.+)$') { $get.content_type = $Matches[1].Trim() }
                        if ($headText -match '(?im)^content-length:\s*(\d+)\s*$') { $get.content_length = [long]$Matches[1] }
                        $get.chunked = [bool]($headText -match '(?im)^transfer-encoding:\s*chunked')
                    }
                }
                if ($hdrEnd -ge 0) {
                    $have = $all.Length - ($hdrEnd + 4)
                    if ($get.content_length -ne $null -and -not $get.chunked -and $have -ge $get.content_length) { $done = $true }
                    if ($get.chunked -and $all.Length -ge 5 -and $all[-5] -eq 48 -and $all[-4] -eq 13 -and $all[-3] -eq 10 -and $all[-2] -eq 13 -and $all[-1] -eq 10) { $done = $true }
                }
            }
            if (-not $get.outcome) {
                $all = $ms.ToArray()
                if ($hdrEnd -lt 0) { $get.outcome = "NO_HTTP_HEADERS" }
                else {
                    $len = $all.Length - ($hdrEnd + 4)
                    # Assigned directly: an empty array returned from an if-expression would unroll to $null.
                    $raw = [byte[]]::new([Math]::Max($len, 0))
                    if ($len -gt 0) { [Array]::Copy($all, $hdrEnd + 4, $raw, 0, $len) }
                    if ($get.chunked) {
                        $d = Dechunk $raw
                        if ($d.ok) { $body = $d.body } else { $get.outcome = $d.error }
                    } elseif ($get.content_length -ne $null) {
                        if ($raw.Length -ne $get.content_length) { $get.outcome = "CONTENT_LENGTH_MISMATCH" } else { $body = $raw }
                    } else { $body = $raw }
                }
            }
        } finally { $client.Dispose() }
    } catch {
        $inner = if ($_.Exception.InnerException) { $_.Exception.InnerException.GetType().Name } else { "" }
        $get.outcome = "GET_FAILED: " + $_.Exception.GetType().Name
        $get.error_message = "$($_.Exception.Message)"; $get.error_inner_type = $inner
    }
    if (-not $get.outcome) { $get.outcome = "RECEIVED" }
    # Evidence writes are guarded so a local I/O error cannot skip the STEP 5 snapshot.
    try {
        if ($null -ne $body) {
            $get.body_bytes = $body.Length
            $get.body_sha256 = ([Security.Cryptography.SHA256]::HashData([byte[]]$body) | ForEach-Object { $_.ToString("x2") }) -join ""
            [IO.File]::WriteAllBytes((Join-Path $EvidenceDir "doc.json"), [byte[]]$body)
        }
        Save "get.json" $get
    } catch { $get.evidence_write_error = "$($_.Exception.Message)" }

    # ---- STEP 5: post-snapshot, always after the GET ---------------------
    $post = Snapshot "post"
    Save "post.json" $post
    SampleExternal $Started.Id
    $same = $post.listener_unambiguous -and $post.process -and (SameTarget $pre $post)
    $State.continuity = if ($same) { "SAME_BOUND_TARGET" } else { "TARGET_INSTANCE_CHANGED" }
    if (-not $same) { Fail "TARGET_INSTANCE_CHANGED" }
    if ($get.remote_endpoint -and $get.remote_endpoint -ne "127.0.0.1:$Port") { Fail "DESTINATION_MISMATCH" }

    # ---- B1: schema availability (semantic) ------------------------------
    $doc = $null
    if ($get.outcome -eq "RECEIVED" -and $get.status_code -eq 200 -and "$($get.content_type)" -match 'json') {
        try { $doc = [Text.Encoding]::UTF8.GetString($body) | ConvertFrom-Json -AsHashtable -Depth 200 } catch { $doc = $null }
    }
    $State.b1 = ($doc -is [hashtable] -and $doc.ContainsKey("paths") -and $doc["paths"] -is [hashtable])
    if (-not $State.b1) { Fail ("SCHEMA_UNAVAILABLE: " + $get.outcome + " / HTTP " + $get.status_code) }

    # ---- STEP 6 (mechanical part): schema inventory ----------------------
    if ($State.b1 -and $same) {
        $routes = [System.Collections.Generic.List[object]]::new()
        foreach ($p in ($doc["paths"].Keys | Sort-Object)) {
            foreach ($m in ($doc["paths"][$p].Keys | Sort-Object)) {
                if ($m -in @("get", "post", "put", "patch", "delete", "head", "options")) {
                    $op = $doc["paths"][$p][$m]
                    $routes.Add([ordered]@{ method = $m.ToUpperInvariant(); path = $p
                        operation_id = if ($op -is [hashtable] -and $op.ContainsKey("operationId")) { $op["operationId"] } else { $null } })
                }
            }
        }
        $schemas = @()
        if ($doc.ContainsKey("components") -and $doc["components"] -is [hashtable] -and $doc["components"].ContainsKey("schemas")) {
            $schemas = @($doc["components"]["schemas"].Keys | Sort-Object)
        }
        $idFields = [System.Collections.Generic.SortedSet[string]]::new()
        $stack = [System.Collections.Generic.Stack[object]]::new(); $stack.Push($doc)
        while ($stack.Count -gt 0) {
            $node = $stack.Pop()
            if ($node -is [hashtable]) {
                if ($node.ContainsKey("properties") -and $node["properties"] -is [hashtable]) {
                    foreach ($k in $node["properties"].Keys) { if ($k -match '(?i)(id|handle|operation|request|job|task)') { [void]$idFields.Add($k) } }
                }
                foreach ($v in $node.Values) { if ($v -is [hashtable] -or $v -is [System.Collections.IList]) { $stack.Push($v) } }
            } elseif ($node -is [System.Collections.IList]) {
                foreach ($v in $node) { if ($v -is [hashtable] -or $v -is [System.Collections.IList]) { $stack.Push($v) } }
            }
        }
        Save "schema-inventory.json" ([ordered]@{
            openapi = if ($doc.ContainsKey("openapi")) { $doc["openapi"] } else { $null }
            info = if ($doc.ContainsKey("info")) { $doc["info"] } else { $null }
            path_count = $doc["paths"].Count; route_count = $routes.Count; schema_count = $schemas.Count
            routes = $routes; schemas = $schemas; candidate_identifier_fields = @($idFields)
        })
    }
}
catch {
    if ($_.Exception.Message -ne "stop") { Fail ("HARNESS_DEFECT: " + $_.Exception.GetType().Name + ": " + $_.Exception.Message) }
}
finally {
    # ---- TEARDOWN (each action guarded) ----------------------------------
    $td = [ordered]@{ stopped_pid = $null; descendants_before_stop = @(); stop_error = $null; port_free_after = $null; isolated_home_files = $null }
    if ($Started) {
        try { $td.descendants_before_stop = @((ProcessTree $Started.Id) -ne $Started.Id) } catch { $td.stop_error = "tree: " + $_.Exception.Message }
        try { if (-not $Started.HasExited) { Stop-Process -Id $Started.Id -Force; $td.stopped_pid = $Started.Id; Start-Sleep -Seconds 1 } }
        catch { $td.stop_error = "stop: " + $_.Exception.Message }
    }
    try { $td.port_free_after = (@(Listeners).Count -eq 0) } catch { $td.port_free_after = "unknown: " + $_.Exception.Message }
    try { $td.isolated_home_files = @(Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue (Join-Path $EvidenceDir "opencode-home")).Count } catch {}
    try { Save "teardown.json" $td } catch {}
    try {
        if ("$($State.reason)" -like "HARNESS_DEFECT*") { $State.awaiting = "HARNESS_DEFECT_REVIEW" }
        elseif ($State.reason) { $State.final_verdict = "EVIDENCE_INSUFFICIENT" }
        else { $State.awaiting = "STEP6_CASE_ANALYSIS_C_TO_H" }
        Save "result.json" ([ordered]@{
            counters = $Counters; state = $State; observed_external_connections = @($Observed)
            reason_mapping = "every reason above maps to EVIDENCE_INSUFFICIENT except when awaiting STEP 6"
            finished_utc = (Get-Date).ToUniversalTime().ToString("o")
        })
    } catch { Write-Error "result.json could not be written: $($_.Exception.Message)" }
}
