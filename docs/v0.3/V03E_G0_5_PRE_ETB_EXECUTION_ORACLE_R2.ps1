# DevRelay v0.3-E - G0.5-PRE / SIC - ETB EXECUTION ORACLE-R2 (normative executable)
#
# ASCII-ONLY SOURCE. Every byte of this file MUST be <= 0x7F.
# The U+2014 em dash required by the result artifact is constructed at runtime
# with [char]0x2014 and written through [System.Text.UTF8Encoding]::new($false).
#
# This file IS the oracle. It must be executed directly from its tracked path.
# It must not be extracted, regenerated, translated, wrapped, patched or
# supplemented with executor-authored assertions.
#
# Semantic inheritance: Mode P pre-existing target; owner endpoint
# http://127.0.0.1:4096; no endpoint discovery; no fallback; no IPv6; no
# localhost alias; no alternate port; no Mode L; no OpenCode start/restart;
# no HTTP; no /doc; no /session; no provider/model call; listener uniqueness;
# OwningProcess; PID; Win32_Process; ExecutablePath; canonicalization; exact
# path equality; executable SHA-256; exact OpenCode version; CreationDate
# process-instance identity; S0/S1 continuity; fail-closed; no retry.

$ErrorActionPreference = 'Stop'
Set-Location 'D:\DevRelay'
$Inv = [System.Globalization.CultureInfo]::InvariantCulture

# ---------------------------------------------------------------- constants
$OracleR2SpecPath   = 'docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.md'
$OracleR2ScriptPath = 'docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1'
$OriginalOracleCommit = '1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc'
$OriginalOracleSha    = '01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921'
$AcceptedTargetRaw = 'C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe'
$ExpectedSha       = '578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35'
$ExpectedVersion   = '1.18.11'
$PackageRoot       = 'C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai'
$PackageManifest   = 'C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\package.json'

$EvF = 'docs/v0.3/evidence/etb-execution-r2/ETB_EVIDENCE.json'
$EvT = 'docs/v0.3/evidence/etb-execution-r2/ETB_EVIDENCE.json.tmp'
$MfF = 'docs/v0.3/evidence/etb-execution-r2/MANIFEST.sha256'
$MfT = 'docs/v0.3/evidence/etb-execution-r2/MANIFEST.sha256.tmp'
$RsF = 'docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_R2.md'
$RsT = 'docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_R2.md.tmp'
$R2Dir = 'docs/v0.3/evidence/etb-execution-r2'

$Started = [System.DateTimeOffset]::UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss.fffffff'Z'", $Inv)
$Outcome = 'HARNESS_INVALID'
$ListenerProbeOutcome = 'NOT_REACHED'
$TerminalStage = ''

$Checks = [ordered]@{
  config_exact='NOT_REACHED'; listener_unique='NOT_REACHED'; listener_fields='NOT_REACHED'
  process_unique='NOT_REACHED'; process_fields='NOT_REACHED'; creation_identity='NOT_REACHED'
  process_path_canonicalized='NOT_REACHED'; target_path_canonicalized='NOT_REACHED'
  canonical_path_equal='NOT_REACHED'; observed_hash_equal='NOT_REACHED'; target_hash_equal='NOT_REACHED'
  package_name_equal='NOT_REACHED'; package_version_equal='NOT_REACHED'; package_bin_equal='NOT_REACHED'
  s0_valid='NOT_REACHED'; s1_valid='NOT_REACHED'; s0_s1_equal='NOT_REACHED'; no_shopping='PASS'
}

function Test-CommandAvailable([string]$name) {
  $c = Get-Command -Name $name -ErrorAction SilentlyContinue
  return ($null -ne $c)
}

function New-Snapshot {
  return [ordered]@{
    mode='MODE_P'; endpoint_scheme='http'; endpoint_address_family='IPv4'; endpoint_host='127.0.0.1'
    endpoint_port=4096; endpoint_base_uri='http://127.0.0.1:4096'; configured_base_url=$script:Configured
    listener_local_address=''; listener_local_port=0; listener_state=''; listener_owning_pid=0
    process_pid=0; process_creation_date_iso=''; process_creation_date_ticks=0
    process_executable_path_raw=''; process_executable_path_canonical=''
    accepted_target_path_raw=$AcceptedTargetRaw; accepted_target_path_canonical=''
    observed_executable_sha256=''; accepted_target_sha256=$ExpectedSha
    package_name=''; package_version=''; package_bin_opencode=''
    expected_sha256=$ExpectedSha; expected_version=$ExpectedVersion
  }
}

# Native canonicalization helper. Only the P/Invoke invocation itself is
# wrapped, because the original frozen taxonomy explicitly classifies a
# type-load / entry-point / marshaling / signature invocation exception as
# HARNESS_INVALID. No listener or snapshot logic is inside this helper.
function Get-CanonicalPath([string]$path) {
  $buffer = [System.Text.StringBuilder]::new(32768)
  $handle = [IntPtr]::Zero
  try {
    $handle = [DevRelayEtbNativeV1]::CreateFileW($path, [uint32]0x80000000, [uint32]0x00000007, [IntPtr]::Zero, [uint32]3, [uint32]0x00000080, [IntPtr]::Zero)
  } catch {
    return @{ kind='HARNESS_INVALID'; reason='native_invocation_exception' }
  }
  if ($handle -eq [System.IntPtr](-1)) { return @{ kind='ETB_UNSATISFIED'; reason='createfile_invalid_handle' } }
  $length = [uint32]0
  try {
    $length = [DevRelayEtbNativeV1]::GetFinalPathNameByHandleW($handle, $buffer, [uint32]32768, [uint32]0)
  } catch {
    try { [void][DevRelayEtbNativeV1]::CloseHandle($handle) } catch { }
    return @{ kind='HARNESS_INVALID'; reason='native_invocation_exception' }
  }
  $closed = $false
  try { $closed = [DevRelayEtbNativeV1]::CloseHandle($handle) } catch { $closed = $false }
  if (-not $closed) { return @{ kind='HARNESS_INVALID'; reason='closehandle_false' } }
  if (($length -eq 0) -or ($length -ge 32768)) { return @{ kind='ETB_UNSATISFIED'; reason='finalpath_length_invalid' } }
  return @{ kind='OK'; path=$buffer.ToString(0, [int]$length) }
}

# ------------------------------------------------- step 1: oracle identity
# The tracked script and spec are the immutable artifacts; their identity is
# bound by the Recovery-R2 authorization and by the independent review. The
# script records the observed digests so the executed bytes are auditable.
$ScriptSelfSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $OracleR2ScriptPath).Hash.ToLower()
$SpecSelfSha   = (Get-FileHash -Algorithm SHA256 -LiteralPath $OracleR2SpecPath).Hash.ToLower()
Write-Output ('ORACLE_R2_SCRIPT_SHA256=' + $ScriptSelfSha)
Write-Output ('ORACLE_R2_SPEC_SHA256=' + $SpecSelfSha)

# ------------------------------- step 2: authoritative config (read-only)
# Frozen rows: python cannot be resolved/launched, an import/dependency/runtime
# failure before the production loader executes -> HARNESS_INVALID.
# A normally returned value that is not the frozen owner URI -> ETB_UNSATISFIED.
$Configured = ''
$ConfigReaderOk = $true
if (-not (Test-CommandAvailable 'python')) {
  $ConfigReaderOk = $false
} else {
  $cfgOut = $null
  try {
    $cfgOut = & python -c "import sys; from devrelay.config import load_wiring_config; sys.stdout.write(load_wiring_config(sys.argv[1]).opencode.base_url)" 'D:\DevRelay' 2>$null
  } catch {
    $ConfigReaderOk = $false
  }
  if ($ConfigReaderOk) {
    if ($LASTEXITCODE -ne 0) { $ConfigReaderOk = $false } else { $Configured = ($cfgOut -join '') }
  }
}
$script:Configured = $Configured
if (-not $ConfigReaderOk) {
  $Checks['config_exact']='FAIL'
  $Outcome = 'HARNESS_INVALID'
  $TerminalStage = 'config_reader_failure'
} elseif ($Configured -ceq 'http://127.0.0.1:4096') {
  $Checks['config_exact']='PASS'
} else {
  $Checks['config_exact']='FAIL'
  $Outcome = 'ETB_UNSATISFIED'
  $TerminalStage = 'config_mismatch'
}

# ------------- infrastructure command availability (before listener stage)
# Frozen original rows: an unavailable command/module is HARNESS_INVALID.
# These branches are mechanically distinct from the listener query itself.
$InfraMissing = ''
foreach ($cmd in @('Get-NetTCPConnection','Get-CimInstance','Get-FileHash','ConvertTo-Json','ConvertFrom-Json','Add-Type')) {
  if (-not (Test-CommandAvailable $cmd)) { $InfraMissing = $cmd }
}
if ($InfraMissing -ne '') {
  $Outcome = 'HARNESS_INVALID'
  $TerminalStage = 'infrastructure_command_unavailable:' + $InfraMissing
  if ($InfraMissing -eq 'Get-NetTCPConnection') { $ListenerProbeOutcome = 'COMMAND_UNAVAILABLE' }
}

# ------------------------------------------- native type load (HARNESS row)
if ($TerminalStage -eq '') {
  $nativeSource = @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class DevRelayEtbNativeV1
{
    [DllImport(
        "kernel32.dll",
        EntryPoint = "CreateFileW",
        CharSet = CharSet.Unicode,
        ExactSpelling = true,
        SetLastError = true)]
    public static extern IntPtr CreateFileW(
        [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
        UInt32 dwDesiredAccess,
        UInt32 dwShareMode,
        IntPtr lpSecurityAttributes,
        UInt32 dwCreationDisposition,
        UInt32 dwFlagsAndAttributes,
        IntPtr hTemplateFile);

    [DllImport(
        "kernel32.dll",
        EntryPoint = "GetFinalPathNameByHandleW",
        CharSet = CharSet.Unicode,
        ExactSpelling = true,
        SetLastError = true)]
    public static extern UInt32 GetFinalPathNameByHandleW(
        IntPtr hFile,
        [Out] StringBuilder lpszFilePath,
        UInt32 cchFilePath,
        UInt32 dwFlags);

    [DllImport(
        "kernel32.dll",
        EntryPoint = "CloseHandle",
        ExactSpelling = true,
        SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool CloseHandle(
        IntPtr hObject);
}
'@
  try {
    Add-Type -TypeDefinition $nativeSource -Language CSharp -ErrorAction Stop
  } catch {
    $Outcome = 'HARNESS_INVALID'
    $TerminalStage = 'native_type_load_failure'
  }
}

# ------------------------------------------------------ snapshot evaluation
function Take-Snapshot {
  $s = New-Snapshot
  $listenerOutcome = 'NOT_REACHED'

  # --- exact frozen listener query with its own narrow boundary ---
  $qerr = @()
  $rows = @()
  try {
    $rows = @(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096 -State Listen -ErrorAction SilentlyContinue -ErrorVariable qerr)
  } catch {
    return @{ kind='ETB_UNSATISFIED'; listener='QUERY_EXCEPTION'; stage='listener'; reason='listener_query_exception'; snapshot=$s }
  }
  if ($qerr.Count -gt 0) {
    $notFound = $false
    foreach ($e in $qerr) { if ([string]$e.FullyQualifiedErrorId -like '*CmdletizationQuery_NotFound*') { $notFound = $true } }
    if ($notFound -and ($rows.Count -eq 0)) {
      return @{ kind='ETB_UNSATISFIED'; listener='ZERO_ROWS'; stage='listener'; reason='listener_zero_rows'; snapshot=$s }
    }
    return @{ kind='ETB_UNSATISFIED'; listener='QUERY_EXCEPTION'; stage='listener'; reason='listener_query_error'; snapshot=$s }
  }
  if ($rows.Count -eq 0) {
    return @{ kind='ETB_UNSATISFIED'; listener='ZERO_ROWS'; stage='listener'; reason='listener_zero_rows'; snapshot=$s }
  }
  if ($rows.Count -gt 1) {
    return @{ kind='ETB_UNSATISFIED'; listener='MULTIPLE_ROWS'; stage='listener'; reason='listener_multiple_rows'; snapshot=$s }
  }

  # --- exactly one row: frozen field and PID validation ---
  $row = $rows[0]
  $pidInt = 0
  $pidOk = $false
  if ($null -ne $row.OwningProcess) { $pidOk = [int]::TryParse([string]$row.OwningProcess, [ref]$pidInt) }
  if (($row.LocalAddress -cne '127.0.0.1') -or ($row.LocalPort -ne 4096) -or ($row.State -ne 'Listen') -or (-not $pidOk) -or ($pidInt -le 0)) {
    return @{ kind='ETB_UNSATISFIED'; listener='FIELD_OR_PID_INVALID'; stage='listener'; reason='listener_field_or_pid_invalid'; snapshot=$s }
  }
  $listenerOutcome = 'ONE_VALID_ROW'
  $Checks['listener_unique']='PASS'; $Checks['listener_fields']='PASS'
  $s['listener_local_address']=[string]$row.LocalAddress; $s['listener_local_port']=[int]$row.LocalPort
  $s['listener_state']=[string]$row.State; $s['listener_owning_pid']=[int]$pidInt

  # --- exact PID-scoped process query with its own narrow boundary ---
  $prows = @()
  try {
    $prows = @(Get-CimInstance -Namespace root/cimv2 -ClassName Win32_Process -Filter ("ProcessId = {0}" -f $pidInt) -ErrorAction Stop)
  } catch {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='process'; reason='process_query_exception'; snapshot=$s }
  }
  if ($prows.Count -ne 1) {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='process'; reason=('process_count_' + $prows.Count); snapshot=$s }
  }
  $prow = $prows[0]
  if ($prow.ProcessId -ne $pidInt) {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='process'; reason='process_pid_mismatch'; snapshot=$s }
  }
  if ([string]::IsNullOrWhiteSpace([string]$prow.ExecutablePath)) {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='process'; reason='executable_path_unavailable'; snapshot=$s }
  }
  if ($null -eq $prow.CreationDate) {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='process'; reason='creation_date_unavailable'; snapshot=$s }
  }
  $dt = $null
  try { $dt = [datetime]$prow.CreationDate } catch {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='process'; reason='creation_date_unreadable'; snapshot=$s }
  }
  $Checks['process_unique']='PASS'; $Checks['process_fields']='PASS'; $Checks['creation_identity']='PASS'
  $s['process_pid']=[int]$pidInt; $s['process_creation_date_iso']=$dt.ToString('o', $Inv); $s['process_creation_date_ticks']=[int64]$dt.Ticks
  $s['process_executable_path_raw']=[string]$prow.ExecutablePath

  # --- canonicalization of the process path and of the accepted target ---
  $cp = Get-CanonicalPath ([string]$prow.ExecutablePath)
  if ($cp.kind -eq 'HARNESS_INVALID') { return @{ kind='HARNESS_INVALID'; listener=$listenerOutcome; stage='process_path'; reason=$cp.reason; snapshot=$s } }
  if ($cp.kind -eq 'ETB_UNSATISFIED') { return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='process_path'; reason=$cp.reason; snapshot=$s } }
  $Checks['process_path_canonicalized']='PASS'; $s['process_executable_path_canonical']=$cp.path
  $ct = Get-CanonicalPath $AcceptedTargetRaw
  if ($ct.kind -eq 'HARNESS_INVALID') { return @{ kind='HARNESS_INVALID'; listener=$listenerOutcome; stage='target_path'; reason=$ct.reason; snapshot=$s } }
  if ($ct.kind -eq 'ETB_UNSATISFIED') { return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='target_path'; reason=$ct.reason; snapshot=$s } }
  $Checks['target_path_canonicalized']='PASS'; $s['accepted_target_path_canonical']=$ct.path
  if ($cp.path -cne $ct.path) {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='canonical_equal'; reason='canonical_path_inequality'; snapshot=$s }
  }
  $Checks['canonical_path_equal']='PASS'

  # --- executable SHA-256 on both paths ---
  $ho = ''
  $ht = ''
  try {
    $ho = (Get-FileHash -Algorithm SHA256 -LiteralPath ([string]$prow.ExecutablePath)).Hash.ToLower()
    $ht = (Get-FileHash -Algorithm SHA256 -LiteralPath $AcceptedTargetRaw).Hash.ToLower()
  } catch {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='hash'; reason='hash_file_unreadable'; snapshot=$s }
  }
  $s['observed_executable_sha256']=$ho; $s['accepted_target_sha256']=$ht
  if ($ho -ine $ExpectedSha) {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='observed_hash'; reason='observed_hash_mismatch'; snapshot=$s }
  }
  $Checks['observed_hash_equal']='PASS'
  if ($ht -ine $ExpectedSha) {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='target_hash'; reason='target_hash_mismatch'; snapshot=$s }
  }
  $Checks['target_hash_equal']='PASS'

  # --- exact version through the frozen package manifest ---
  if (-not (Test-Path -LiteralPath $PackageManifest -PathType Leaf)) {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='package'; reason='package_manifest_missing'; snapshot=$s }
  }
  $pkg = $null
  try { $pkg = Get-Content -LiteralPath $PackageManifest -Raw | ConvertFrom-Json } catch {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='package'; reason='package_manifest_malformed'; snapshot=$s }
  }
  if ($pkg.name -cne 'opencode-ai') {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='package_name'; reason='package_name_mismatch'; snapshot=$s }
  }
  $Checks['package_name_equal']='PASS'
  if ($pkg.version -cne '1.18.11') {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='package_version'; reason='package_version_mismatch'; snapshot=$s }
  }
  $Checks['package_version_equal']='PASS'
  $s['package_name']=[string]$pkg.name; $s['package_version']=[string]$pkg.version
  $binDeclared = [string]$pkg.bin.opencode
  $s['package_bin_opencode']=$binDeclared
  $cb = Get-CanonicalPath (Join-Path $PackageRoot $binDeclared)
  if ($cb.kind -eq 'HARNESS_INVALID') { return @{ kind='HARNESS_INVALID'; listener=$listenerOutcome; stage='package_bin'; reason=$cb.reason; snapshot=$s } }
  if ($cb.kind -eq 'ETB_UNSATISFIED') { return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='package_bin'; reason=$cb.reason; snapshot=$s } }
  if ($cb.path -cne $ct.path) {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='package_bin'; reason='package_bin_path_inequality'; snapshot=$s }
  }
  $Checks['package_bin_equal']='PASS'
  return @{ kind='OK'; listener=$listenerOutcome; stage='complete'; snapshot=$s }
}

$S0 = $null
$S1 = $null

if ($TerminalStage -eq '') {
  $S0 = Take-Snapshot
  $ListenerProbeOutcome = $S0.listener
  if ($S0.kind -eq 'HARNESS_INVALID') { $Outcome='HARNESS_INVALID'; $TerminalStage='s0_' + $S0.stage }
  elseif ($S0.kind -eq 'ETB_UNSATISFIED') { $Outcome='ETB_UNSATISFIED'; $TerminalStage='s0_' + $S0.stage }
  else {
    $Checks['s0_valid']='PASS'
    $S1 = Take-Snapshot
    if ($S1.kind -eq 'HARNESS_INVALID') { $Outcome='HARNESS_INVALID'; $TerminalStage='s1_' + $S1.stage }
    elseif ($S1.kind -eq 'ETB_UNSATISFIED') { $Outcome='ETB_UNSATISFIED'; $TerminalStage='s1_' + $S1.stage }
    else {
      $Checks['s1_valid']='PASS'
      $fields = @('endpoint_scheme','endpoint_address_family','endpoint_host','endpoint_port','endpoint_base_uri','configured_base_url','listener_local_address','listener_local_port','listener_state','listener_owning_pid','process_pid','process_creation_date_ticks','process_executable_path_raw','process_executable_path_canonical','accepted_target_path_canonical','observed_executable_sha256','accepted_target_sha256','package_name','package_version','package_bin_opencode')
      $equal = $true
      foreach ($f in $fields) { if ($S0.snapshot[$f] -cne $S1.snapshot[$f]) { $equal = $false } }
      if ($equal) { $Checks['s0_s1_equal']='PASS'; $Outcome='ETB_SATISFIED' } else { $Checks['s0_s1_equal']='FAIL'; $Outcome='ETB_UNSATISFIED' }
    }
  }
}

if ($null -eq $S0) { $S0 = @{ snapshot = New-Snapshot } }
if ($null -eq $S1) { $S1 = @{ snapshot = New-Snapshot } }
$Finished = [System.DateTimeOffset]::UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss.fffffff'Z'", $Inv)

Write-Output ('ORACLE_R2_SEMANTIC outcome=' + $Outcome + ' listener_probe_outcome=' + $ListenerProbeOutcome + ' terminal_stage=' + $TerminalStage)
Write-Output ('ORACLE_R2_CHECKS ' + (($Checks.GetEnumerator() | ForEach-Object { $_.Key + '=' + $_.Value }) -join ' '))

# ------------------------- evidence and publication stage (delimited region)
# This region contains NO listener, process, canonicalization, hash or package
# logic. It only serializes the already-decided semantic result and publishes
# the three frozen R2 outputs. A failure here is the frozen HARNESS_INVALID
# evidence-machinery classification.
$PublicationFailed = $false
$EvDigest = ''
$MfDigest = ''
$PublicationError = ''
try {
  $Evidence = [ordered]@{
    schema_version = 'devrelay-etb-v1'
    oracle_commit = $OriginalOracleCommit
    oracle_sha256 = $OriginalOracleSha
    execution_started_at = $Started
    execution_finished_at = $Finished
    mode = 'MODE_P'
    endpoint = [ordered]@{ scheme='http'; address_family='IPv4'; host='127.0.0.1'; port=4096; base_uri='http://127.0.0.1:4096'; fallback='NONE' }
    configured_base_url = $Configured
    target = [ordered]@{ package_name='opencode-ai'; expected_version=$ExpectedVersion; expected_executable=$AcceptedTargetRaw; expected_sha256=$ExpectedSha; package_root=$PackageRoot; package_manifest=$PackageManifest }
    snapshot_s0 = $S0.snapshot
    snapshot_s1 = $S1.snapshot
    checks = $Checks
    listener_probe_outcome = $ListenerProbeOutcome
    outcome = $Outcome
    non_claims = @('not_sic_result','not_p6_result','not_g0_5_result','not_mode_b_result','not_case_c_authorization','not_adoption_authorization')
    activity_counters = [ordered]@{ web_network=0; endpoint_discovery=0; port_scan=0; listener_scan=0; process_scan=0; opencode_start=0; http=0; doc=0; session=0; provider_model=0; sic_attempts=0; mode_b_oracle_work=0; g0_5=0; g1_g2=0 }
  }

  # --- R2 six-path precondition: file OR directory occupancy fails closed ---
  $occupied = @()
  foreach ($p in @($EvF,$EvT,$MfF,$MfT,$RsF,$RsT)) {
    if (([System.IO.File]::Exists($p)) -or ([System.IO.Directory]::Exists($p))) { $occupied += $p }
  }
  if ($occupied.Count -gt 0) { throw ('R2_OUTPUT_PATH_OCCUPIED:' + ($occupied -join ',')) }
  if ([System.IO.File]::Exists($R2Dir)) { throw 'R2_OUTPUT_DIR_IS_FILE' }
  if (-not [System.IO.Directory]::Exists($R2Dir)) { [void][System.IO.Directory]::CreateDirectory($R2Dir) }
  if (-not [System.IO.Directory]::Exists($R2Dir)) { throw 'R2_OUTPUT_DIR_CREATE_FAILED' }

  $enc = [System.Text.UTF8Encoding]::new($false)
  $json = $Evidence | ConvertTo-Json -Depth 12 -Compress
  $evBytes = $enc.GetBytes($json + "`n")
  $fs = [System.IO.FileStream]::new($EvT,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
  try { $fs.Write($evBytes,0,$evBytes.Length); $fs.Flush($true) } finally { $fs.Dispose() }
  $rb = [System.IO.File]::ReadAllBytes($EvT)
  if ($rb.Length -ne $evBytes.Length) { throw 'EVIDENCE_TEMP_LENGTH_MISMATCH' }
  for ($i=0; $i -lt $evBytes.Length; $i++) { if ($rb[$i] -ne $evBytes[$i]) { throw 'EVIDENCE_TEMP_BYTE_MISMATCH' } }
  if ($rb[$rb.Length-1] -ne 10) { throw 'EVIDENCE_TEMP_NO_FINAL_LF' }
  if (($rb[$rb.Length-2] -eq 10) -or ($rb[$rb.Length-2] -eq 13)) { throw 'EVIDENCE_TEMP_EXTRA_LF' }
  if (($rb[0] -eq 0xEF) -and ($rb[1] -eq 0xBB) -and ($rb[2] -eq 0xBF)) { throw 'EVIDENCE_TEMP_BOM' }
  $parsed = [System.Text.Encoding]::UTF8.GetString($rb) | ConvertFrom-Json
  if ($parsed.schema_version -cne 'devrelay-etb-v1') { throw 'EVIDENCE_SCHEMA_VERSION_MISMATCH' }
  if ($parsed.outcome -cne $Outcome) { throw 'EVIDENCE_OUTCOME_MISMATCH' }
  if ($parsed.listener_probe_outcome -cne $ListenerProbeOutcome) { throw 'EVIDENCE_LISTENER_PROBE_OUTCOME_MISMATCH' }

  $sha = [System.Security.Cryptography.SHA256]::Create()
  $EvDigest = (($sha.ComputeHash($evBytes) | ForEach-Object { $_.ToString('x2') }) -join '')
  $mfBytes = $enc.GetBytes($EvDigest + '  ' + $EvF + "`n")
  $fs2 = [System.IO.FileStream]::new($MfT,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
  try { $fs2.Write($mfBytes,0,$mfBytes.Length); $fs2.Flush($true) } finally { $fs2.Dispose() }
  $mrb = [System.IO.File]::ReadAllBytes($MfT)
  if ($mrb.Length -ne $mfBytes.Length) { throw 'MANIFEST_TEMP_LENGTH_MISMATCH' }
  for ($i=0; $i -lt $mfBytes.Length; $i++) { if ($mrb[$i] -ne $mfBytes[$i]) { throw 'MANIFEST_TEMP_BYTE_MISMATCH' } }
  $mfLine = ($enc.GetString($mrb)).TrimEnd("`n")
  if ($mfLine.Substring(0,64) -cne $EvDigest) { throw 'MANIFEST_DIGEST_MISMATCH' }
  if ($mfLine.Substring(64,2) -cne '  ') { throw 'MANIFEST_SPACES_MISMATCH' }
  if ($mfLine.Substring(66) -cne $EvF) { throw 'MANIFEST_PATH_MISMATCH' }
  $MfDigest = (($sha.ComputeHash($mfBytes) | ForEach-Object { $_.ToString('x2') }) -join '')

  # The em dash is constructed at runtime from an ASCII-only source so the
  # result artifact contains the exact UTF-8 bytes E2 80 94 for U+2014.
  $EmDash = [char]0x2014
  $OutcomeText = if ($Outcome -eq 'HARNESS_INVALID') { 'HARNESS_INVALID / NO ETB SEMANTIC RESULT' } else { $Outcome }
  $lines = @(
    ('DEVRELAY v0.3-E ETB EXECUTION RESULT ' + $EmDash + ' CANDIDATE'),
    '',
    'Status:',
    'CANDIDATE ETB RESULT / AWAITING INDEPENDENT RESULT REVIEW',
    '',
    'Outcome:',
    $OutcomeText,
    '',
    'Oracle commit:',
    $OriginalOracleCommit,
    '',
    'Oracle SHA-256:',
    $OriginalOracleSha,
    '',
    'Evidence SHA-256:',
    $EvDigest,
    '',
    'Manifest SHA-256:',
    $MfDigest,
    '',
    'Execution started UTC:',
    $Started,
    '',
    'Execution finished UTC:',
    $Finished,
    '',
    'Non-claims:',
    'NOT SIC',
    'NOT P6',
    'NOT G0.5',
    'NOT MODE-B RESULT',
    'NOT CASE-C AUTHORIZATION',
    'NOT ADOPTION AUTHORIZATION',
    '',
    'No result artifact is authoritative before independent review.'
  )
  $rsBytes = $enc.GetBytes(($lines -join "`n") + "`n")
  $fs3 = [System.IO.FileStream]::new($RsT,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
  try { $fs3.Write($rsBytes,0,$rsBytes.Length); $fs3.Flush($true) } finally { $fs3.Dispose() }
  $rrb = [System.IO.File]::ReadAllBytes($RsT)
  if ($rrb.Length -ne $rsBytes.Length) { throw 'RESULT_TEMP_LENGTH_MISMATCH' }
  for ($i=0; $i -lt $rsBytes.Length; $i++) { if ($rrb[$i] -ne $rsBytes[$i]) { throw 'RESULT_TEMP_BYTE_MISMATCH' } }
  if (($rrb[0] -eq 0xEF) -and ($rrb[1] -eq 0xBB) -and ($rrb[2] -eq 0xBF)) { throw 'RESULT_TEMP_BOM' }
  $dash = $enc.GetBytes([string]$EmDash)
  $dashIdx = -1
  for ($i=0; $i -lt ($rrb.Length - 2); $i++) {
    if (($rrb[$i] -eq $dash[0]) -and ($rrb[$i+1] -eq $dash[1]) -and ($rrb[$i+2] -eq $dash[2])) { $dashIdx = $i; break }
  }
  if ($dashIdx -lt 0) { throw 'RESULT_TEMP_EM_DASH_MISSING' }

  # --- publication order: evidence, then manifest, then result LAST ---
  [System.IO.File]::Move($EvT,$EvF)
  $f1 = [System.IO.File]::ReadAllBytes($EvF)
  if ($f1.Length -ne $evBytes.Length) { throw 'EVIDENCE_FINAL_LENGTH_MISMATCH' }
  for ($i=0; $i -lt $evBytes.Length; $i++) { if ($f1[$i] -ne $evBytes[$i]) { throw 'EVIDENCE_FINAL_BYTE_MISMATCH' } }
  [System.IO.File]::Move($MfT,$MfF)
  $f2 = [System.IO.File]::ReadAllBytes($MfF)
  if ($f2.Length -ne $mfBytes.Length) { throw 'MANIFEST_FINAL_LENGTH_MISMATCH' }
  for ($i=0; $i -lt $mfBytes.Length; $i++) { if ($f2[$i] -ne $mfBytes[$i]) { throw 'MANIFEST_FINAL_BYTE_MISMATCH' } }
  [System.IO.File]::Move($RsT,$RsF)
  $f3 = [System.IO.File]::ReadAllBytes($RsF)
  if ($f3.Length -ne $rsBytes.Length) { throw 'RESULT_FINAL_LENGTH_MISMATCH' }
  for ($i=0; $i -lt $rsBytes.Length; $i++) { if ($f3[$i] -ne $rsBytes[$i]) { throw 'RESULT_FINAL_BYTE_MISMATCH' } }

  $pf = [System.Text.Encoding]::UTF8.GetString($f1) | ConvertFrom-Json
  if ($pf.outcome -cne $Outcome) { throw 'POST_EVIDENCE_OUTCOME_MISMATCH' }
  if ($pf.listener_probe_outcome -cne $ListenerProbeOutcome) { throw 'POST_LISTENER_PROBE_OUTCOME_MISMATCH' }
  $pfDigest = (($sha.ComputeHash($f1) | ForEach-Object { $_.ToString('x2') }) -join '')
  $mfFinalLine = ($enc.GetString($f2)).TrimEnd("`n")
  if ($mfFinalLine.Substring(0,64) -cne $pfDigest) { throw 'POST_MANIFEST_DIGEST_MISMATCH' }
  if ($mfFinalLine.Substring(66) -cne $EvF) { throw 'POST_MANIFEST_PATH_MISMATCH' }
} catch {
  $PublicationFailed = $true
  $PublicationError = [string]$_.Exception.Message
}

# ------------------------------------------------------- terminal reporting
# MANDATORY STOP: nothing after this point may probe the endpoint, listeners,
# processes, commands or any diagnostic surface. The attempt is terminal.
if ($PublicationFailed) {
  Write-Output ('ORACLE_R2_PUBLICATION_FAILURE ' + $PublicationError)
  Write-Output 'ORACLE_R2_FINAL_CLASSIFICATION=HARNESS_INVALID'
  Write-Output 'ORACLE_R2_SEMANTIC_RESULT=NONE'
  exit 3
}

Write-Output 'ORACLE_R2_PUBLICATION_OK'
Write-Output ('ORACLE_R2_EVIDENCE_SHA256=' + $EvDigest)
Write-Output ('ORACLE_R2_MANIFEST_SHA256=' + $MfDigest)
Write-Output ('ORACLE_R2_FINAL_CLASSIFICATION=' + $Outcome)
if ($Outcome -eq 'HARNESS_INVALID') {
  Write-Output 'ORACLE_R2_SEMANTIC_RESULT=NONE'
} else {
  Write-Output ('ORACLE_R2_SEMANTIC_RESULT=' + $Outcome)
}
exit 0
