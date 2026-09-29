# DevRelay v0.3-E - G0.5-PRE / SIC - ETB EXECUTION ORACLE-PATHE (normative executable)
#
# Identity: Oracle-PathE. Canonical identity token: PATH_E.
# Historical predecessor oracle: Oracle-PathD
#   (docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1), which is FROZEN and
#   is NOT modified, wrapped, sourced, patched or reused at runtime by this file.
#
# DESIGN CANDIDATE. NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE.
# This file does not authorize execution and consumes no budget.
#
# ---------------------------------------------------------------------------
# BOOTSTRAP-ORDER CORRECTION (the reason this oracle exists)
# ---------------------------------------------------------------------------
# Historical reviewed Oracle-PathD defect (independently confirmed, NOT repaired
# in the frozen Path-D artifact): Get-FileHash was USED unprotected at lines
# 117/118 for oracle self-identity, while command availability was only CHECKED
# later, at line 189, inside a gate whose list itself contains Get-FileHash. The
# gate was therefore unreachable in exactly the scenario it exists to handle,
# and the terminating CommandNotFoundException escaped before any classification
# or publication, surfacing as an undocumented exit code 1.
#
# Oracle-PathE removes that failure mode by construction:
#   (1) an explicit BOOTSTRAP SAFETY PHASE (step 0) runs before every other
#       stage and uses no cmdlet to decide whether other facilities exist;
#   (2) oracle self-identity hashing uses the .NET SHA-256 primitive, which
#       follows from the PowerShell/.NET runtime already required to execute
#       this script, so Get-FileHash is never needed at all;
#   (3) a top-level guard converts any residual unexpected host/internal
#       failure into an explicit, documented terminal state instead of an
#       accidental exit code;
#   (4) ALL reporting uses the .NET stdout primitive [System.Console]::Out,
#       never a cmdlet, so that no reporting surface (least of all the guard
#       itself) depends on a facility that step 0 may have just found
#       unavailable;
#   (5) the guard's own emergency reporting is itself wrapped, so a failure of
#       the reporting channel cannot prevent the guard's frozen
#       process-control exit code.
# Invariants enforced by design:
#   AVAILABILITY-CHECK STAGE < FIRST-USE STAGE for every gated facility;
#   NO UNGATED CMDLET OR EXTERNAL EXECUTABLE IS EVER INVOKED;
#   AN EXCEPTION INSIDE THE EMERGENCY REPORTING PATH CANNOT PREVENT EXIT 4.
#
# ASCII-ONLY SOURCE. Every byte of this file MUST be <= 0x7F.
# The U+2014 em dash required by the result artifact is constructed at runtime
# with [char]0x2014 and written through [System.Text.UTF8Encoding]::new($false).
#
# This file IS the oracle. It must be executed directly from its tracked path.
# It must not be extracted, regenerated, translated, wrapped, patched or
# supplemented with executor-authored assertions.
#
# Semantic inheritance (unchanged from Oracle-PathD): Mode P pre-existing
# target; owner endpoint http://127.0.0.1:4096; no endpoint discovery; no
# fallback; no IPv6; no localhost alias; no alternate port; no Mode L; no
# OpenCode start/restart; no HTTP; no /doc; no /session; no provider/model
# call; listener uniqueness; OwningProcess; PID; Win32_Process; ExecutablePath;
# canonicalization; exact path equality; executable SHA-256; exact OpenCode
# version; CreationDate process-instance identity; S0/S1 continuity;
# fail-closed; no retry; no fallback; no automatic repair.
#
# Result classes (exactly three, unchanged): ETB_SATISFIED; ETB_UNSATISFIED;
# HARNESS_INVALID / NO ETB SEMANTIC RESULT. No fourth class exists, and the
# historical Path-D governance phrase "UNCLASSIFIED CONTROL FAILURE" is NOT a
# class of this oracle.
#
# Exit-code contract (explicit and total; no accidental path):
#   0 = oracle completed and PUBLISHED one of the three result classes
#   2 = EXPECTED INFRASTRUCTURE FAILURE classified by the oracle, but the
#       result could not be published because a publication facility was itself
#       unavailable. This branch is reached BEFORE any output path is created,
#       so no output artifact exists (fail-closed).
#   3 = publication/control stage failed after the semantic outcome was decided.
#       This code does NOT mean "no output artifact exists": a control failure
#       can occur after one or more FINAL moves have already happened, so
#       artifact presence MUST be inspected on disk and MUST NOT be inferred
#       from the exit code alone.
#   4 = UNEXPECTED internal or host failure reached the top-level guard
#       (fail-closed). The guard emits a frozen classification when its
#       reporting channel is usable; a failure of that channel does not change
#       the exit code. The guard can also catch a failure raised after a
#       successful publication (for example by the terminal reporting write),
#       so artifact presence MUST likewise be inspected on disk rather than
#       inferred from this exit code.
# Any other value is a defect, not a contract.

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# UNEXPECTED-FAILURE GUARD (top-level, installed before anything else runs)
# ---------------------------------------------------------------------------
# Expected infrastructure failures are classified by the explicit branches below
# and never reach this guard. The publication region has its own narrow
# try/catch and never reaches this guard either. This guard exists only for an
# UNEXPECTED internal or host failure for which no designed branch applies: it
# converts such a failure into the documented fail-closed terminal state instead
# of an accidental exit code. Consistent with the inherited frozen discipline,
# no exception message, stack, provider text or environment data is captured,
# persisted or printed here.
#
# The guard invokes NO cmdlet. Its reporting uses the .NET stdout primitive
# only, and that reporting is itself wrapped: if emergency reporting fails (for
# example because the stdout channel is unavailable or closed), the inner catch
# suppresses ONLY that reporting failure and `exit 4` still runs. `exit 4` is
# deliberately outside the inner try/catch so that no reporting failure can
# prevent the frozen process-control termination.
trap {
  try {
    [System.Console]::Out.WriteLine('ORACLE_PATH_E_UNEXPECTED_HOST_FAILURE')
    [System.Console]::Out.WriteLine('ORACLE_PATH_E_FINAL_CLASSIFICATION=HARNESS_INVALID')
    [System.Console]::Out.WriteLine('ORACLE_PATH_E_SEMANTIC_RESULT=NONE')
  } catch {
  }
  exit 4
}

# Repository-root binding. The frozen repository root is derived
# deterministically from the tracked script location: this file lives at
# <repo>/docs/v0.3/, so the grandparent of $PSScriptRoot is <repo>. No absolute
# repository path is hard-coded. .NET is used rather than Split-Path /
# Set-Location so that bootstrap does not depend on any cmdlet.
$RepoRoot = [System.IO.Path]::GetDirectoryName([System.IO.Path]::GetDirectoryName($PSScriptRoot))
[System.IO.Directory]::SetCurrentDirectory($RepoRoot)
$Inv = [System.Globalization.CultureInfo]::InvariantCulture

# ---------------------------------------------------------------- constants
$OraclePathESpecPath   = 'docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md'
$OraclePathEScriptPath = 'docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1'
$OriginalOracleCommit = '1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc'
$OriginalOracleSha    = '01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921'
# Path-E specific provenance is UNKNOWN until a future independent approval
# record populates it. It is never inferred, defaulted or fabricated here.
$OraclePathECommit = 'UNKNOWN'
$OraclePathESpecSha = 'UNKNOWN'
$OraclePathEScriptSha = 'UNKNOWN'
$AcceptedTargetRaw = 'C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe'
$ExpectedSha       = '578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35'
$ExpectedVersion   = '1.18.11'
$PackageRoot       = 'C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai'
$PackageManifest   = 'C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\package.json'

$EvF = 'docs/v0.3/evidence/etb-execution-path-e/ETB_EVIDENCE.json'
$EvT = 'docs/v0.3/evidence/etb-execution-path-e/ETB_EVIDENCE.json.tmp'
$MfF = 'docs/v0.3/evidence/etb-execution-path-e/MANIFEST.sha256'
$MfT = 'docs/v0.3/evidence/etb-execution-path-e/MANIFEST.sha256.tmp'
$RsF = 'docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_E.md'
$RsT = 'docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_E.md.tmp'
$PathEDir = 'docs/v0.3/evidence/etb-execution-path-e'

$Started = [System.DateTimeOffset]::UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss.fffffff'Z'", $Inv)
$Outcome = 'HARNESS_INVALID'
$ListenerProbeOutcome = 'NOT_REACHED'
$TerminalStage = ''
$HostFailureStage = ''
$ExitCode = 0

$Checks = [ordered]@{
  config_exact='NOT_REACHED'; listener_unique='NOT_REACHED'; listener_fields='NOT_REACHED'
  process_unique='NOT_REACHED'; process_fields='NOT_REACHED'; creation_identity='NOT_REACHED'
  process_path_canonicalized='NOT_REACHED'; target_path_canonicalized='NOT_REACHED'
  canonical_path_equal='NOT_REACHED'; observed_hash_equal='NOT_REACHED'; target_hash_equal='NOT_REACHED'
  package_name_equal='NOT_REACHED'; package_version_equal='NOT_REACHED'; package_bin_equal='NOT_REACHED'
  s0_valid='NOT_REACHED'; s1_valid='NOT_REACHED'; s0_s1_equal='NOT_REACHED'; no_shopping='PASS'
}

# ---------------------------------------------------------------------------
# step 0: BOOTSTRAP SAFETY PHASE  (runs before every other stage)
# ---------------------------------------------------------------------------
# Assumed bootstrap primitives, available because this script is executing under
# Windows PowerShell / .NET at all: PowerShell language constructs (statements,
# functions, operators, arrays, ordered hashtables, foreach, try/catch/finally,
# throw, trap); type literals for System.* types; static .NET members of the
# runtime libraries already loaded (System.IO.Path, System.IO.File,
# System.IO.Directory, System.IO.FileStream, System.Text.StringBuilder,
# System.Text.UTF8Encoding, System.Text.Encoding,
# System.Security.Cryptography.SHA256, System.DateTimeOffset,
# System.Console, System.Globalization.CultureInfo). None of these is a cmdlet.
#
# System.Console is the frozen reporting primitive. It is a .NET static type of
# the same runtime layer that is already required to execute this script at all,
# it is not a PowerShell cmdlet, and it is the ONLY output channel this file
# uses: deterministic single-line stdout reporting through
# [System.Console]::Out.WriteLine. A write through it returns nothing and adds
# nothing to the PowerShell pipeline. If that channel is unavailable or closed
# the write throws like any other .NET call: at step 6 the top-level guard
# converts it into the frozen exit 4, and inside the guard an emergency-report
# failure is swallowed so the process-control exit code is unaffected.
#
# Everything else is a GATED FACILITY and is availability-checked here, before
# its first operational use anywhere in this file. Test-BootstrapFacility is
# itself wrapped in try/catch so that the failure of the checker (Get-Command
# unavailable) is reported as an unavailable facility instead of terminating
# the script.
function Test-BootstrapFacility([string]$name) {
  try {
    $c = Get-Command -Name $name -ErrorAction Stop
    return ($null -ne $c)
  } catch {
    return $false
  }
}

# Gated facilities and their first operational use (check stage 0 < use stage):
#   python             : step 2 config reader subprocess          (line region "step 2")
#   Add-Type           : step 3 native canonicalization type load
#   Get-NetTCPConnection : step 4 listener query inside Take-Snapshot
#   Get-CimInstance    : step 4 process query inside Take-Snapshot
#   ConvertTo-Json     : step 5 evidence serialization (publication region)
#   ConvertFrom-Json   : step 4 package manifest parse; step 5 readback validation
# Get-FileHash is deliberately NOT gated because Oracle-PathE NEVER uses it.
# Write-Output and ForEach-Object are NOT gated either, because Oracle-PathE
# never uses them: reporting goes through [System.Console]::Out and iteration
# uses the foreach language statement.
$GatedFacilities = @('python','Add-Type','Get-NetTCPConnection','Get-CimInstance','ConvertTo-Json','ConvertFrom-Json')
$MissingFacilities = @()
foreach ($fac in $GatedFacilities) {
  if (-not (Test-BootstrapFacility $fac)) { $MissingFacilities += $fac }
}
$BootstrapOk = ($MissingFacilities.Count -eq 0)
$CanSerialize = (Test-BootstrapFacility 'ConvertTo-Json')
$CanValidateJson = (Test-BootstrapFacility 'ConvertFrom-Json')
$BootstrapMissing = $MissingFacilities -join ','
[System.Console]::Out.WriteLine('ORACLE_PATH_E_BOOTSTRAP ok=' + $BootstrapOk + ' missing=' + $BootstrapMissing)
if (-not $BootstrapOk) {
  $Outcome = 'HARNESS_INVALID'
  $TerminalStage = 'infrastructure_command_unavailable:' + $MissingFacilities[0]
  if ($MissingFacilities -contains 'Get-NetTCPConnection') { $ListenerProbeOutcome = 'COMMAND_UNAVAILABLE' }
}

# step 1: oracle identity (self-hashing).
# Uses .NET SHA-256 only. It must not depend on Get-FileHash, and it must not
# run before the bootstrap phase above has already established whether the
# facilities this script relies on exist.
function Get-Utf8FileSha256([string]$path) {
  $bytes = [System.IO.File]::ReadAllBytes($path)
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    $hash = $sha.ComputeHash($bytes)
    $sb = [System.Text.StringBuilder]::new(64)
    foreach ($b in $hash) { [void]$sb.Append($b.ToString('x2')) }
    return $sb.ToString()
  } finally {
    $sha.Dispose()
  }
}
# step 1a: lowercase-hex rendering of a digest, used by the publication region.
# Language-level iteration only (foreach): no cmdlet and no pipeline command is
# involved. Defined here, before its first use in step 5.
function Get-LowerHex([byte[]]$bytes) {
  $sb = [System.Text.StringBuilder]::new(($bytes.Length * 2))
  foreach ($b in $bytes) { [void]$sb.Append($b.ToString('x2')) }
  return $sb.ToString()
}

$ScriptSelfSha = Get-Utf8FileSha256 $OraclePathEScriptPath
$SpecSelfSha   = Get-Utf8FileSha256 $OraclePathESpecPath
[System.Console]::Out.WriteLine('ORACLE_PATH_E_SCRIPT_SHA256=' + $ScriptSelfSha)
[System.Console]::Out.WriteLine('ORACLE_PATH_E_SPEC_SHA256=' + $SpecSelfSha)

# step 2: authoritative config (read-only).
# Frozen rows: python cannot be resolved/launched, or an import/dependency/runtime
# failure before the production loader executes -> HARNESS_INVALID.
# A normally returned value that is not the frozen owner URI -> ETB_UNSATISFIED.
# Oracle-PathE reads the manifest with .NET rather than Get-Content, and manages
# PYTHONPATH through the .NET environment API, so the only gated dependency of
# this stage is the python executable itself.
$Configured = ''
$ConfigReaderOk = $true
if (($TerminalStage -ne '') -or (-not (Test-BootstrapFacility 'python'))) {
  $ConfigReaderOk = $false
} elseif ($TerminalStage -eq '') {
  $cfgOut = $null
  $cfgExit = -1
  $priorPythonPath = [System.Environment]::GetEnvironmentVariable('PYTHONPATH','Process')
  $savedErrorActionPreference = $ErrorActionPreference
  try {
    [System.Environment]::SetEnvironmentVariable('PYTHONPATH', [System.IO.Path]::Combine($RepoRoot,'src'), 'Process')
    $ErrorActionPreference = 'Continue'
    $cfgOut = & python -c "import sys; from devrelay.config import load_wiring_config; sys.stdout.write(load_wiring_config(sys.argv[1]).opencode.base_url)" $RepoRoot 2>$null
    $cfgExit = $LASTEXITCODE
  } catch {
    $ConfigReaderOk = $false
  } finally {
    $ErrorActionPreference = $savedErrorActionPreference
    if ($null -ne $priorPythonPath) { [System.Environment]::SetEnvironmentVariable('PYTHONPATH', $priorPythonPath, 'Process') }
    else { [System.Environment]::SetEnvironmentVariable('PYTHONPATH', $null, 'Process') }
  }
  if ($ConfigReaderOk) {
    if ($cfgExit -ne 0) { $ConfigReaderOk = $false } else { $Configured = ($cfgOut -join '') }
  }
}
$script:Configured = $Configured
if ($TerminalStage -ne '') {
  # bootstrap already decided a terminal infrastructure outcome; config is not
  # evaluated and no later stage may run.
  $Checks['config_exact']='NOT_REACHED'
} elseif (-not $ConfigReaderOk) {
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

# step 3: native type load (HARNESS row).
if ($TerminalStage -eq '') {
  $nativeSource = @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class DevRelayEtbNativePathE
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

# Native canonicalization helper. Only the P/Invoke invocation itself is
# wrapped, because the inherited frozen taxonomy explicitly classifies a
# type-load / entry-point / marshaling / signature invocation exception as
# HARNESS_INVALID. No listener or snapshot logic is inside this helper.
function Get-CanonicalPath([string]$path) {
  $buffer = [System.Text.StringBuilder]::new(32768)
  $handle = [IntPtr]::Zero
  try {
    $handle = [DevRelayEtbNativePathE]::CreateFileW($path, [uint32]0x80000000, [uint32]0x00000007, [IntPtr]::Zero, [uint32]3, [uint32]0x00000080, [IntPtr]::Zero)
  } catch {
    return @{ kind='HARNESS_INVALID'; reason='native_invocation_exception' }
  }
  if ($handle -eq [System.IntPtr](-1)) { return @{ kind='ETB_UNSATISFIED'; reason='createfile_invalid_handle' } }
  $length = [uint32]0
  try {
    $length = [DevRelayEtbNativePathE]::GetFinalPathNameByHandleW($handle, $buffer, [uint32]32768, [uint32]0)
  } catch {
    try { [void][DevRelayEtbNativePathE]::CloseHandle($handle) } catch { }
    return @{ kind='HARNESS_INVALID'; reason='native_invocation_exception' }
  }
  $closed = $false
  try { $closed = [DevRelayEtbNativePathE]::CloseHandle($handle) } catch { $closed = $false }
  if (-not $closed) { return @{ kind='HARNESS_INVALID'; reason='closehandle_false' } }
  if (($length -eq 0) -or ($length -ge 32768)) { return @{ kind='ETB_UNSATISFIED'; reason='finalpath_length_invalid' } }
  return @{ kind='OK'; path=$buffer.ToString(0, [int]$length) }
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

# step 4: snapshot evaluation (the only region that touches the target).
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

  # --- executable SHA-256 on both paths (the .NET primitive; no cmdlet) ---
  $ho = ''
  $ht = ''
  try {
    $ho = Get-Utf8FileSha256 ([string]$prow.ExecutablePath)
    $ht = Get-Utf8FileSha256 $AcceptedTargetRaw
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
  if (-not [System.IO.File]::Exists($PackageManifest)) {
    return @{ kind='ETB_UNSATISFIED'; listener=$listenerOutcome; stage='package'; reason='package_manifest_missing'; snapshot=$s }
  }
  $pkg = $null
  try { $pkg = [System.IO.File]::ReadAllText($PackageManifest) | ConvertFrom-Json } catch {
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
  $cb = Get-CanonicalPath ([System.IO.Path]::Combine($PackageRoot, $binDeclared))
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

# Inherited listener_probe_outcome semantics: the single published field always
# means THE LISTENER PROBE OUTCOME ASSOCIATED WITH THE LAST ACTUALLY EXECUTED
# SNAPSHOT PROBE THAT DETERMINES OR CONTRIBUTES TO THE PUBLISHED TERMINAL
# RESULT. It stays NOT_REACHED when the attempt ends before any listener probe;
# it is the S0 listener outcome when S0 terminates the attempt; it is the S1
# listener outcome when S1 is reached and terminates the attempt; and it remains
# ONE_VALID_ROW when both listener probes succeed even if a later
# continuity/identity check fails. The assignment is total: no executor choice
# between S0 and S1 remains.
if ($TerminalStage -eq '') {
  $S0 = Take-Snapshot
  $ListenerProbeOutcome = $S0.listener
  if ($S0.kind -eq 'HARNESS_INVALID') { $Outcome='HARNESS_INVALID'; $TerminalStage='s0_' + $S0.stage }
  elseif ($S0.kind -eq 'ETB_UNSATISFIED') { $Outcome='ETB_UNSATISFIED'; $TerminalStage='s0_' + $S0.stage }
  else {
    $Checks['s0_valid']='PASS'
    $S1 = Take-Snapshot
    $ListenerProbeOutcome = $S1.listener
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

[System.Console]::Out.WriteLine('ORACLE_PATH_E_SEMANTIC outcome=' + $Outcome + ' listener_probe_outcome=' + $ListenerProbeOutcome + ' terminal_stage=' + $TerminalStage)
$checkParts = @()
foreach ($checkKey in $Checks.Keys) { $checkParts += ($checkKey + '=' + $Checks[$checkKey]) }
[System.Console]::Out.WriteLine('ORACLE_PATH_E_CHECKS ' + ($checkParts -join ' '))

if ((-not $BootstrapOk) -and ((-not $CanSerialize) -or (-not $CanValidateJson))) {
  # EXPECTED INFRASTRUCTURE FAILURE with an unavailable serialization facility:
  # the oracle has classified the outcome but cannot publish it. Fail closed with
  # the documented infrastructure exit code; no output path is created.
  [System.Console]::Out.WriteLine('ORACLE_PATH_E_PUBLICATION_UNAVAILABLE')
  [System.Console]::Out.WriteLine('ORACLE_PATH_E_FINAL_CLASSIFICATION=HARNESS_INVALID')
  [System.Console]::Out.WriteLine('ORACLE_PATH_E_SEMANTIC_RESULT=NONE')
  exit 2
}

# step 5: evidence and publication stage (delimited region).
# This region contains NO listener, process, canonicalization, hash or package
# logic. It only serializes the already-decided semantic result and publishes
# the three frozen Oracle-PathE outputs into the Path-E namespace only. A
# failure here is the frozen HARNESS_INVALID evidence-machinery classification.
$PublicationFailed = $false
$EvDigest = ''
$MfDigest = ''
try {
  $Evidence = [ordered]@{
    schema_version = 'devrelay-etb-v1-path-e'
    oracle_identity = 'Oracle-PathE'
    oracle_canonical_token = 'PATH_E'
    oracle_commit = $OriginalOracleCommit
    oracle_sha256 = $OriginalOracleSha
    oracle_path_e_commit = $OraclePathECommit
    oracle_path_e_spec_sha256 = $OraclePathESpecSha
    oracle_path_e_script_sha256 = $OraclePathEScriptSha
    predecessor_oracle = 'Oracle-PathD'
    predecessor_oracle_defect_recorded = 'Get-FileHash used before its own availability gate; NOT REPAIRED; Path-D exhausted'
    execution_started_at = $Started
    execution_finished_at = $Finished
    mode = 'MODE_P'
    endpoint = [ordered]@{ scheme='http'; address_family='IPv4'; host='127.0.0.1'; port=4096; base_uri='http://127.0.0.1:4096'; fallback='NONE' }
    configured_base_url = $Configured
    target = [ordered]@{ package_name='opencode-ai'; expected_version=$ExpectedVersion; expected_executable=$AcceptedTargetRaw; expected_sha256=$ExpectedSha; package_root=$PackageRoot; package_manifest=$PackageManifest }
    bootstrap = [ordered]@{ phase='step 0'; ok=$BootstrapOk; missing=$BootstrapMissing; gates=@('python','Add-Type','Get-NetTCPConnection','Get-CimInstance','ConvertTo-Json','ConvertFrom-Json'); get_file_hash_used=$false }
    snapshot_s0 = $S0.snapshot
    snapshot_s1 = $S1.snapshot
    checks = $Checks
    listener_probe_outcome = $ListenerProbeOutcome
    outcome = $Outcome
    terminal_stage = $TerminalStage
    non_claims = @('not_sic_result','not_p6_result','not_g0_5_result','not_mode_b_result','not_case_c_authorization','not_adoption_authorization')
    activity_counters = [ordered]@{ web_network=0; endpoint_discovery=0; port_scan=0; listener_scan=0; process_scan=0; opencode_start=0; http=0; doc=0; session=0; provider_model=0; sic_attempts=0; mode_b_oracle_work=0; g0_5=0; g1_g2=0 }
  }

  # Six-path precondition: file OR directory occupancy fails closed.
  $occupied = @()
  foreach ($p in @($EvF,$EvT,$MfF,$MfT,$RsF,$RsT)) {
    if (([System.IO.File]::Exists($p)) -or ([System.IO.Directory]::Exists($p))) { $occupied += $p }
  }
  if ($occupied.Count -gt 0) { throw ('ORACLE_PATH_E_OUTPUT_PATH_OCCUPIED:' + ($occupied -join ',')) }
  if ([System.IO.File]::Exists($PathEDir)) { throw 'ORACLE_PATH_E_OUTPUT_DIR_IS_FILE' }
  if (-not [System.IO.Directory]::Exists($PathEDir)) { [void][System.IO.Directory]::CreateDirectory($PathEDir) }
  if (-not [System.IO.Directory]::Exists($PathEDir)) { throw 'ORACLE_PATH_E_OUTPUT_DIR_CREATE_FAILED' }

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
  if ($parsed.schema_version -cne 'devrelay-etb-v1-path-e') { throw 'EVIDENCE_SCHEMA_VERSION_MISMATCH' }
  if ($parsed.outcome -cne $Outcome) { throw 'EVIDENCE_OUTCOME_MISMATCH' }
  if ($parsed.listener_probe_outcome -cne $ListenerProbeOutcome) { throw 'EVIDENCE_LISTENER_PROBE_OUTCOME_MISMATCH' }

  $sha = [System.Security.Cryptography.SHA256]::Create()
  $EvDigest = Get-LowerHex ($sha.ComputeHash($evBytes))
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
  $MfDigest = Get-LowerHex ($sha.ComputeHash($mfBytes))

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
    'Lineage:',
    'PATH_E / Oracle-PathE',
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
  $pfDigest = Get-LowerHex ($sha.ComputeHash($f1))
  $mfFinalLine = ($enc.GetString($f2)).TrimEnd("`n")
  if ($mfFinalLine.Substring(0,64) -cne $pfDigest) { throw 'POST_MANIFEST_DIGEST_MISMATCH' }
  if ($mfFinalLine.Substring(66) -cne $EvF) { throw 'POST_MANIFEST_PATH_MISMATCH' }
} catch {
  # The publication-failure surface is a constant. No exception message, stack,
  # provider text or environment data is captured, persisted or printed.
  $PublicationFailed = $true
}

# step 6: terminal reporting.
# MANDATORY STOP: nothing after this point may probe the endpoint, listeners,
# processes, commands or any diagnostic surface. The attempt is terminal.
# Reporting uses [System.Console]::Out only; no cmdlet is invoked. If the
# reporting channel itself fails here after a successful publication, the
# failure reaches the top-level guard, which exits 4 without deleting, retrying,
# repairing or rewriting anything: the already-published artifact remains on
# disk, and its presence must be inspected on disk and never inferred from the
# exit code.
if ($PublicationFailed) {
  [System.Console]::Out.WriteLine('ORACLE_PATH_E_PUBLICATION_FAILURE')
  [System.Console]::Out.WriteLine('ORACLE_PATH_E_FINAL_CLASSIFICATION=HARNESS_INVALID')
  [System.Console]::Out.WriteLine('ORACLE_PATH_E_SEMANTIC_RESULT=NONE')
  exit 3
}

[System.Console]::Out.WriteLine('ORACLE_PATH_E_PUBLICATION_OK')
[System.Console]::Out.WriteLine('ORACLE_PATH_E_EVIDENCE_SHA256=' + $EvDigest)
[System.Console]::Out.WriteLine('ORACLE_PATH_E_MANIFEST_SHA256=' + $MfDigest)
[System.Console]::Out.WriteLine('ORACLE_PATH_E_FINAL_CLASSIFICATION=' + $Outcome)
if ($Outcome -eq 'HARNESS_INVALID') {
  [System.Console]::Out.WriteLine('ORACLE_PATH_E_SEMANTIC_RESULT=NONE')
} else {
  [System.Console]::Out.WriteLine('ORACLE_PATH_E_SEMANTIC_RESULT=' + $Outcome)
}
exit 0
