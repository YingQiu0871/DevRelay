# DevRelay v0.3-E - G0.5-PRE / SIC - ETB QUERY_EXCEPTION DIAGNOSTIC D1 (execution script)
#
# ASCII-ONLY SOURCE. Every byte of this file MUST be <= 0x7F.
#
# STATUS OF THIS FILE: tracked design/implementation SOURCE ONLY.
#   D1 IMPLEMENTATION = CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED.
#   This file MUST NOT be executed until an independently accepted execution authorization
#   and its independently confirmed bookkeeping exist. This construction round does not run it.
#
# AUTHORITATIVE DESIGN (C2-clarified, accepted):
#   diagnostic_d1_design_commit = 14b85bd2365d500ef87f357aeecb94de14211cc9
#   diagnostic_d1_spec_sha256   = 69b7cfda172658fe6c4e726430274a27a6dffb4c4d1c90a374d79feb6956e35d
#
# OWNER-SELECTED ACCEPTED C2 POLICY: OPTION B - NORMALIZED TERMINATING-DUPLICATE SUPPRESSION.
#   Implemented exactly as accepted; see the C2 section inside the execution phase.
#
# CORRECTIONS CARRIED BY THIS CANDIDATE (the candidate replaces, but never rewrites, the
# rejected candidate a25e15416dba2c1d31918e6b41824204c219d948):
#   P2   - post-consumption directory occupancy gate (File.Exists OR Directory.Exists)
#          evaluated after BOTH claims are consumed and immediately before directory creation.
#   P3-B - deterministic script-body failure mapping onto the closed six-code set; no known
#          throwing operation is left outside a mapped boundary.
#   P3-A - UNCHANGED AND STILL OPEN: ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN.
#          This candidate serializes complete observed accepted string values. No truncation,
#          no hashing in place of content, no invented maximum size, no dropped long value.
#
# This script is the future execution entrypoint. It is NOT an ETB semantic attempt:
# no observation produced by it may become or replace AUTHORITATIVE ETB SEMANTIC RESULT.
#
# Self-integrity: this script does NOT embed its own commit id or its own expected SHA-256.
# Those arrive as mandatory parameters and are frozen only after independent review and
# acceptance bookkeeping.
#
# ---------------------------------------------------------------------------------------
# THROWING-OPERATION INVENTORY (static, for independent audit)
# The script body is covered by a single script-scope trap that maps every otherwise
# unhandled failure onto the closed set {0,10,20,30,40,50} using the irreversible-stage
# tracker $Stage. Operations that can raise and their mapping boundary:
#   git object access / hashing / worktree reads / config-reader invocation /
#   filesystem existence checks   -> PRE      -> 10 (or explicit precondition failure 10)
#   auth claim byte construction   -> PRE      -> 10   (before the AUTH TEMP CreateNew)
#   auth claim CreateNew/write/flush/readback/move/hash -> AUTH -> 20 (explicit catch)
#   attempt claim byte construction/CreateNew/write/flush/readback/move/hash
#                                  -> ATTEMPT -> 30 (explicit catch)
#   directory occupancy gate / directory creation / command availability /
#   query setup / ErrorRecord normalization / row normalization /
#   evidence byte construction     -> HARNESS -> 40
#   JSON serialization / manifest construction / result construction /
#   output TEMP creation / output Move/readback/hash -> PUBLICATION -> 50
# No reachable failing operation is intentionally left outside these boundaries.

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$AcceptedAuthorizationCommit,
  [Parameter(Mandatory = $true)][string]$ExpectedAuthorizationSha256,
  [Parameter(Mandatory = $true)][string]$ExpectedScriptSha256
)

# ================================================================ exit-code contract
# Closed set: {0,10,20,30,40,50}. Declared first so that the script-body failure mapping
# below can be expressed in terms of them.
# This contract governs the script BODY. PowerShell parser, host and mandatory-parameter
# binding failures happen BEFORE the body is entered: they are outside D1 harness entry,
# can consume no claim and can never represent a D1 result or a D1 observation.
$ExitOk           = 0
$ExitPrecondition = 10
$ExitAuthClaim    = 20
$ExitAttemptClaim = 30
$ExitHarness      = 40
$ExitPublication  = 50

# ========================================================= script-body failure mapping
# Irreversible-stage tracker. Exactly one of: PRE, AUTH, ATTEMPT, HARNESS, PUBLICATION.
# It is only ever advanced, never rolled back.
$Stage = 'PRE'
# 1 only once the single listener-query site has been entered.
$QueryStarted = 0

trap {
  # Deterministic mapping of any otherwise-unhandled failure raised inside the script body
  # onto the closed six-code set. There is no reachable script-body exception path that
  # escapes to the host as an unmapped exit code.
  $stageNow = 'UNKNOWN'
  if ($null -ne $script:Stage) { $stageNow = [string]$script:Stage }
  $code = $script:ExitHarness
  if ($stageNow -eq 'PRE') { $code = $script:ExitPrecondition }
  elseif ($stageNow -eq 'AUTH') { $code = $script:ExitAuthClaim }
  elseif ($stageNow -eq 'ATTEMPT') { $code = $script:ExitAttemptClaim }
  elseif ($stageNow -eq 'PUBLICATION') { $code = $script:ExitPublication }
  $exType = ''
  $exMsg = ''
  if ($null -ne $_) {
    if ($null -ne $_.Exception) {
      $exType = [string]$_.Exception.GetType().FullName
      $exMsg = [string]$_.Exception.Message
    }
  }
  Write-Output ('D1_SCRIPT_BODY_FAILURE_MAPPED=' + [string]$code)
  Write-Output ('D1_SCRIPT_BODY_FAILURE_STAGE=' + $stageNow)
  Write-Output ('D1_SCRIPT_BODY_FAILURE_EXCEPTION_TYPE=' + $exType)
  Write-Output ('D1_SCRIPT_BODY_FAILURE_EXCEPTION_MESSAGE=' + $exMsg)
  Write-Output ('D1_LISTENER_QUERY_STARTED=' + [string]$script:QueryStarted)
  Write-Output 'D1_BUDGET_ROLLBACK_INFERRED=0'
  Write-Output 'D1_CLAIM_FILES_ARE_FORENSIC_SOURCE=1'
  Write-Output 'D1_RETRY_AUTHORIZED=0'
  Write-Output 'D1_SECOND_QUERY_AUTHORIZED=0'
  exit $code
}

$ErrorActionPreference = 'Stop'

# Repository root is derived deterministically from the tracked script location:
# this file lives at <repo>/docs/v0.3/, so the grandparent of $PSScriptRoot is <repo>.
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location -LiteralPath $RepoRoot
$Inv = [System.Globalization.CultureInfo]::InvariantCulture

# ------------------------------------------------------- fixed design constants
$SchemaVersion = 'devrelay-etb-query-diagnostic-d1-v1'
$DiagnosticMode = 'QUERY_EXCEPTION_DIAGNOSTIC_D1'
$EndpointUri = 'http://127.0.0.1:4096'

# Accepted C2 design authority. This is the DESIGN commit, never a bookkeeping commit.
$DesignCommit = '14b85bd2365d500ef87f357aeecb94de14211cc9'
$DesignSpecSha = '69b7cfda172658fe6c4e726430274a27a6dffb4c4d1c90a374d79feb6956e35d'

$SourceBookkeepingCommit = '93e44fe61c59ec5070e2823062a607347bb9163a'
$SourceR2EvidenceSha = '6f903f05e859a05a99dc0cde253e878ae7235c1554e212ab2f6b27945b2da0c8'
$SourceR2ManifestSha = 'b4701c900132ffee9d9f31ac7c7137c906da80de97a08678544c7d7d7eb522c1'
$SourceR2ResultSha = '84f51bb5d7765112cb65376ea164e10780bb777f1beb6e962d6baa4508fe9efa'
$SourceR2AuthClaimSha = 'fd7336e4694f8d491ddd3067880851f96974a29a1117d48f7dd47eb2d629ccf7'
$SourceR2AttemptClaimSha = '69eb6ef0352375311f72c211d04c8ed39e59d8f7b00b6d7738577044916167f9'

$ConfigSha = 'b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf'
$ConfigSize = 1897

$SpecPath = 'docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_SPEC.md'
$AuthorizationRel = 'docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION_AUTHORIZATION.md'
$ScriptRel = 'docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION.ps1'

$R2EvidencePath = 'docs/v0.3/evidence/etb-execution-r2/ETB_EVIDENCE.json'
$R2ManifestPath = 'docs/v0.3/evidence/etb-execution-r2/MANIFEST.sha256'
$R2ResultPath = 'docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_R2.md'
$R2AuthClaimPath = 'docs/v0.3/evidence/ETB_RECOVERY_R2_AUTHORIZATION_USE.claim'
$R2AttemptClaimPath = 'docs/v0.3/evidence/ETB_RECOVERY_R2_ATTEMPT_USE.claim'
$ConfigPath = '.devrelay/config.yaml'

# claim namespace (TEMP / FINAL), permanently distinct from R1 / R2 namespaces
$AuthTemp = 'docs/v0.3/evidence/ETB_QUERY_DIAGNOSTIC_D1_AUTHORIZATION_USE.claim.tmp'
$AuthFinal = 'docs/v0.3/evidence/ETB_QUERY_DIAGNOSTIC_D1_AUTHORIZATION_USE.claim'
$AttemptTemp = 'docs/v0.3/evidence/ETB_QUERY_DIAGNOSTIC_D1_ATTEMPT_USE.claim.tmp'
$AttemptFinal = 'docs/v0.3/evidence/ETB_QUERY_DIAGNOSTIC_D1_ATTEMPT_USE.claim'

# output namespace (TEMP / FINAL)
$EvDir = 'docs/v0.3/evidence/etb-query-diagnostic-d1'
$EvFinal = 'docs/v0.3/evidence/etb-query-diagnostic-d1/QUERY_DIAGNOSTIC_EVIDENCE.json'
$EvTemp = 'docs/v0.3/evidence/etb-query-diagnostic-d1/QUERY_DIAGNOSTIC_EVIDENCE.json.tmp'
$MfFinal = 'docs/v0.3/evidence/etb-query-diagnostic-d1/MANIFEST.sha256'
$MfTemp = 'docs/v0.3/evidence/etb-query-diagnostic-d1/MANIFEST.sha256.tmp'
$RsFinal = 'docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_DIAGNOSTIC_RESULT_D1.md'
$RsTemp = 'docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_DIAGNOSTIC_RESULT_D1.md.tmp'

$ClaimSchemaAuth = 'devrelay-etb-query-diagnostic-d1-authorization-use-v1'
$ClaimSchemaAttempt = 'devrelay-etb-query-diagnostic-d1-attempt-use-v1'

$JsonDepth = 12
$StampFormat = "yyyy-MM-dd'T'HH:mm:ss.fffffff'Z'"

# frozen non_claims array: exactly 13 strings, exact order, never derived or reworded
$NonClaims = @(
  'does not establish ETB_SATISFIED',
  'does not establish a replacement ETB_UNSATISFIED',
  'does not establish P6 PASS',
  'does not establish P6 FAIL',
  'does not establish G0.5 PASS',
  'does not establish G0.5 FAIL',
  'does not authorize Mode-B',
  'does not establish OpenCode general compatibility or incompatibility',
  'does not establish permanent endpoint state',
  'does not establish permanent listener state',
  'does not establish process binding',
  'does not establish target executable identity',
  'does not establish Oracle-R2 general correctness or incorrectness'
)

# ------------------------------------------------------------------- helpers
function Test-CommandAvailable([string]$name) {
  $c = Get-Command -Name $name -ErrorAction SilentlyContinue
  return ($null -ne $c)
}

function Test-Occupied([string]$relPath) {
  # Occupancy means a FILE or a DIRECTORY at that path.
  $abs = Join-Path $RepoRoot $relPath
  return ([System.IO.File]::Exists($abs) -or [System.IO.Directory]::Exists($abs))
}

function Test-BytesEqual([byte[]]$a, [byte[]]$b) {
  if ($null -eq $a -or $null -eq $b) { return $false }
  if ($a.Length -ne $b.Length) { return $false }
  for ($i = 0; $i -lt $a.Length; $i++) { if ($a[$i] -ne $b[$i]) { return $false } }
  return $true
}

function Get-FileSha256([string]$absPath) {
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    $fs = [System.IO.File]::OpenRead($absPath)
    try { $hash = $sha.ComputeHash($fs) } finally { $fs.Dispose() }
  } finally { $sha.Dispose() }
  return (($hash | ForEach-Object { $_.ToString('x2') }) -join '')
}

function Get-UtcStamp {
  return [System.DateTimeOffset]::UtcNow.ToString($StampFormat, $Inv)
}

function Get-GitBlobSha256([string]$commit, [string]$relPath) {
  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = 'git'
  $psi.Arguments = '-C "' + $RepoRoot + '" cat-file blob ' + $commit + ':' + $relPath
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $p = [System.Diagnostics.Process]::Start($psi)
  $ms = [System.IO.MemoryStream]::new()
  $p.StandardOutput.BaseStream.CopyTo($ms)
  $p.WaitForExit()
  if ($p.ExitCode -ne 0) { $ms.Dispose(); return $null }
  $bytes = $ms.ToArray()
  $ms.Dispose()
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try { $hash = $sha.ComputeHash($bytes) } finally { $sha.Dispose() }
  return (($hash | ForEach-Object { $_.ToString('x2') }) -join '')
}

function Test-GitCommit([string]$commit) {
  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = 'git'
  $psi.Arguments = '-C "' + $RepoRoot + '" cat-file -t ' + $commit
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $p = [System.Diagnostics.Process]::Start($psi)
  $out = $p.StandardOutput.ReadToEnd().Trim()
  $p.WaitForExit()
  return (($p.ExitCode -eq 0) -and ($out -eq 'commit'))
}

function Get-Text([object]$value) {
  if ($null -eq $value) { return '' }
  return ([string]$value)
}

function New-ErrorRecordObject([object]$rec, [string]$source) {
  # Exactly the accepted 15 ordered fields, every one a JSON string, unavailable -> "".
  # P3-A standing: the complete observed string value is carried, never truncated.
  $fqid = ''
  $cat = ''
  $catAct = ''
  $catReason = ''
  $catTargetName = ''
  $catTargetType = ''
  $exType = ''
  $exMsg = ''
  $exHr = ''
  $inType = ''
  $inMsg = ''
  $edMsg = ''
  $invPos = ''
  $stack = ''
  if ($null -ne $rec) {
    $fqid = Get-Text $rec.FullyQualifiedErrorId
    $cat = Get-Text $rec.CategoryInfo.Category
    $catAct = Get-Text $rec.CategoryInfo.Activity
    $catReason = Get-Text $rec.CategoryInfo.Reason
    $catTargetName = Get-Text $rec.CategoryInfo.TargetName
    $catTargetType = Get-Text $rec.CategoryInfo.TargetType
    $ex = $rec.Exception
    if ($null -ne $ex) {
      $exType = Get-Text $ex.GetType().FullName
      $exMsg = Get-Text $ex.Message
      $hr = $ex.HResult
      if ($null -ne $hr) { $exHr = [System.Convert]::ToString([int]$hr, $Inv) }
      $inner = $ex.InnerException
      if ($null -ne $inner) {
        $inType = Get-Text $inner.GetType().FullName
        $inMsg = Get-Text $inner.Message
      }
    }
    $edMsg = Get-Text $rec.ErrorDetails.Message
    $invPos = Get-Text $rec.InvocationInfo.PositionMessage
    $stack = Get-Text $rec.ScriptStackTrace
  }
  return [ordered]@{
    source                    = $source
    fully_qualified_error_id  = $fqid
    category                  = $cat
    category_activity         = $catAct
    category_reason           = $catReason
    category_target_name      = $catTargetName
    category_target_type      = $catTargetType
    exception_type            = $exType
    exception_message         = $exMsg
    exception_hresult         = $exHr
    inner_exception_type      = $inType
    inner_exception_message   = $inMsg
    error_details_message     = $edMsg
    invocation_position_message = $invPos
    script_stack_trace        = $stack
  }
}

function Test-RecordPayloadEqual([object]$a, [object]$b) {
  # C2 Option B comparison: exactly these 14 payload fields, in the accepted order,
  # ordinal string equality. `source` is the only excluded field, and it is excluded
  # because the two records legitimately carry different channel labels.
  # No case folding, no culture-aware comparison, no partial or subset comparison,
  # no message-only / fully-qualified-id-only / exception-type-only comparison,
  # no reference identity, no object identity, no hashing, no timing heuristic.
  $keys = @(
    'fully_qualified_error_id', 'category', 'category_activity', 'category_reason',
    'category_target_name', 'category_target_type', 'exception_type', 'exception_message',
    'exception_hresult', 'inner_exception_type', 'inner_exception_message',
    'error_details_message', 'invocation_position_message', 'script_stack_trace'
  )
  foreach ($k in $keys) {
    if (-not [string]::Equals([string]$a[$k], [string]$b[$k], [System.StringComparison]::Ordinal)) {
      return $false
    }
  }
  return $true
}

function New-ClaimBytes([string]$schemaVersion, [string]$designCommit, [string]$designSpecSha,
                        [string]$authCommit, [string]$authSha, [string]$scriptSha) {
  # Exact serialization: UTF-8, no BOM, LF-only, exactly one terminal LF, one field per line,
  # <field_name>=<value>\n in the exact frozen order, no quoting, no spaces around '='.
  $sb = [System.Text.StringBuilder]::new()
  $fields = [ordered]@{
    schema_version                            = $schemaVersion
    diagnostic_d1_design_commit               = $designCommit
    diagnostic_d1_spec_sha256                 = $designSpecSha
    diagnostic_d1_authorization_commit        = $authCommit
    diagnostic_d1_authorization_sha256        = $authSha
    diagnostic_d1_script_sha256               = $scriptSha
    source_authoritative_bookkeeping_commit   = $SourceBookkeepingCommit
    source_r2_evidence_sha256                 = $SourceR2EvidenceSha
    source_r2_result_sha256                   = $SourceR2ResultSha
    source_r2_authorization_claim_sha256      = $SourceR2AuthClaimSha
    source_r2_attempt_claim_sha256            = $SourceR2AttemptClaimSha
    state                                     = 'CONSUMED'
  }
  foreach ($k in $fields.Keys) {
    [void]$sb.Append($k).Append('=').Append([string]$fields[$k]).Append("`n")
  }
  $enc = [System.Text.UTF8Encoding]::new($false)
  return $enc.GetBytes($sb.ToString())
}

function Write-AtomicFile([string]$relTemp, [string]$relFinal, [byte[]]$bytes) {
  # TEMP CreateNew -> write -> Flush(true) -> close -> readback -> two-argument Move -> readback.
  $absTemp = Join-Path $RepoRoot $relTemp
  $absFinal = Join-Path $RepoRoot $relFinal
  $fs = [System.IO.FileStream]::new($absTemp, [System.IO.FileMode]::CreateNew,
                                    [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
  try { $fs.Write($bytes, 0, $bytes.Length); $fs.Flush($true) } finally { $fs.Dispose() }
  $back = [System.IO.File]::ReadAllBytes($absTemp)
  if (-not (Test-BytesEqual $back $bytes)) { return $false }
  [System.IO.File]::Move($absTemp, $absFinal)
  $back2 = [System.IO.File]::ReadAllBytes($absFinal)
  if (-not (Test-BytesEqual $back2 $bytes)) { return $false }
  return $true
}

function Get-ListenerRow([object]$row) {
  # Only the accepted row fields, frozen order. LocalPort / OwningProcess: observed integer
  # or null. LocalAddress / State: observed string or "".
  # NOTE: the local variable must not be named `pid`; `$PID` is a read-only PowerShell
  # automatic variable and assigning to it raises SessionStateUnauthorizedAccessException.
  $addr = ''
  $state = ''
  $port = $null
  $owningProcess = $null
  if ($null -ne $row.LocalAddress) { $addr = [string]$row.LocalAddress }
  if ($null -ne $row.State) { $state = [string]$row.State }
  if ($null -ne $row.LocalPort) { $port = [int]$row.LocalPort }
  if ($null -ne $row.OwningProcess) { $owningProcess = [int]$row.OwningProcess }
  return [ordered]@{
    LocalAddress  = $addr
    LocalPort     = $port
    State         = $state
    OwningProcess = $owningProcess
  }
}

# ================================================================== PRECONDITIONS
# Stage PRE. Every precondition A-P is evaluated BEFORE any claim consumption.
# Any failure exits with $ExitPrecondition, without creating a claim or running a query.
$PreOk = $true
$PreFail = ''

# A. accepted D1 design commit and B. accepted D1 spec SHA-256 are compile-time constants above;
#    they are re-verified against the tracked spec file at the accepted commit.
$specAtDesign = Get-GitBlobSha256 $DesignCommit $SpecPath
if ($null -eq $specAtDesign) { $PreOk = $false; $PreFail = 'A_design_commit_unresolved' }
elseif ($specAtDesign -ne $DesignSpecSha) { $PreOk = $false; $PreFail = 'B_design_spec_sha_mismatch' }
elseif (-not (Test-Path -LiteralPath (Join-Path $RepoRoot $SpecPath))) { $PreOk = $false; $PreFail = 'B_design_spec_absent' }
else {
  $specNow = Get-FileSha256 (Join-Path $RepoRoot $SpecPath)
  if ($specNow -ne $DesignSpecSha) { $PreOk = $false; $PreFail = 'B_worktree_spec_sha_mismatch' }
}

# C. the accepted authorization commit resolves to an exact Git commit.
if ($PreOk) { if (-not (Test-GitCommit $AcceptedAuthorizationCommit)) { $PreOk = $false; $PreFail = 'C_authorization_commit_unresolved' } }

# D. authorization artifact at that commit hashes to ExpectedAuthorizationSha256.
if ($PreOk) {
  $authAtCommit = Get-GitBlobSha256 $AcceptedAuthorizationCommit $AuthorizationRel
  if ($null -eq $authAtCommit) { $PreOk = $false; $PreFail = 'D_authorization_absent_at_commit' }
  elseif ($authAtCommit -ne $ExpectedAuthorizationSha256) { $PreOk = $false; $PreFail = 'D_authorization_sha_mismatch' }
}

# E. script at that commit hashes to ExpectedScriptSha256.
if ($PreOk) {
  $scriptAtCommit = Get-GitBlobSha256 $AcceptedAuthorizationCommit $ScriptRel
  if ($null -eq $scriptAtCommit) { $PreOk = $false; $PreFail = 'E_script_absent_at_commit' }
  elseif ($scriptAtCommit -ne $ExpectedScriptSha256) { $PreOk = $false; $PreFail = 'E_script_sha_mismatch' }
}

# F. worktree authorization artifact hash matches expected.
if ($PreOk) {
  $authAbs = Join-Path $RepoRoot $AuthorizationRel
  if (-not (Test-Path -LiteralPath $authAbs)) { $PreOk = $false; $PreFail = 'F_authorization_absent_in_worktree' }
  else { if ((Get-FileSha256 $authAbs) -ne $ExpectedAuthorizationSha256) { $PreOk = $false; $PreFail = 'F_worktree_authorization_sha_mismatch' } }
}

# G. worktree script hash matches expected (self-integrity of the running script).
if ($PreOk) {
  $scriptAbs = Join-Path $RepoRoot $ScriptRel
  if (-not (Test-Path -LiteralPath $scriptAbs)) { $PreOk = $false; $PreFail = 'G_script_absent_in_worktree' }
  else { if ((Get-FileSha256 $scriptAbs) -ne $ExpectedScriptSha256) { $PreOk = $false; $PreFail = 'G_worktree_script_sha_mismatch' } }
}

# H. config SHA / size.
if ($PreOk) {
  $cfgAbs = Join-Path $RepoRoot $ConfigPath
  if (-not (Test-Path -LiteralPath $cfgAbs)) { $PreOk = $false; $PreFail = 'H_config_absent' }
  else {
    if ((Get-Item -LiteralPath $cfgAbs).Length -ne $ConfigSize) { $PreOk = $false; $PreFail = 'H_config_size_mismatch' }
    elseif ((Get-FileSha256 $cfgAbs) -ne $ConfigSha) { $PreOk = $false; $PreFail = 'H_config_sha_mismatch' }
  }
}

# I. frozen config reader returns exactly the accepted endpoint.
#    Reuses the accepted Recovery-R2 reader contract verbatim, including PYTHONPATH save/restore.
$Configured = ''
if ($PreOk) {
  if (-not (Test-CommandAvailable 'python')) { $PreOk = $false; $PreFail = 'I_python_unavailable' }
  else {
    $cfgOut = $null
    $cfgExit = -1
    $PriorPythonPathExists = Test-Path -LiteralPath 'Env:PYTHONPATH'
    $PriorPythonPath = $env:PYTHONPATH
    $SavedEap = $ErrorActionPreference
    try {
      $env:PYTHONPATH = (Join-Path $RepoRoot 'src')
      $ErrorActionPreference = 'Continue'
      $cfgOut = & python -c "import sys; from devrelay.config import load_wiring_config; sys.stdout.write(load_wiring_config(sys.argv[1]).opencode.base_url)" $RepoRoot 2>$null
      $cfgExit = $LASTEXITCODE
    } finally {
      $ErrorActionPreference = $SavedEap
      if ($PriorPythonPathExists) { $env:PYTHONPATH = $PriorPythonPath }
      else { Remove-Item -LiteralPath 'Env:PYTHONPATH' -ErrorAction SilentlyContinue }
    }
    if ($cfgExit -ne 0) { $PreOk = $false; $PreFail = 'I_config_reader_failed' }
    else {
      $Configured = ($cfgOut -join '')
      if ($Configured -cne $EndpointUri) { $PreOk = $false; $PreFail = 'I_configured_base_url_mismatch' }
    }
  }
}

# J. configured_base_url equals endpoint (explicit redundancy check; never inferred from one another).
if ($PreOk) { if ($Configured -cne $EndpointUri) { $PreOk = $false; $PreFail = 'J_endpoint_config_inequality' } }

# K. R2 evidence / manifest / result hashes.
if ($PreOk) {
  foreach ($pair in @(
      @($R2EvidencePath, $SourceR2EvidenceSha), @($R2ManifestPath, $SourceR2ManifestSha),
      @($R2ResultPath, $SourceR2ResultSha))) {
    $abs = Join-Path $RepoRoot $pair[0]
    if (-not (Test-Path -LiteralPath $abs)) { $PreOk = $false; $PreFail = 'K_r2_artifact_absent' }
    elseif ((Get-FileSha256 $abs) -ne $pair[1]) { $PreOk = $false; $PreFail = 'K_r2_artifact_sha_mismatch' }
  }
}

# L. R2 authorization / attempt claim hashes.
if ($PreOk) {
  foreach ($pair in @(
      @($R2AuthClaimPath, $SourceR2AuthClaimSha), @($R2AttemptClaimPath, $SourceR2AttemptClaimSha))) {
    $abs = Join-Path $RepoRoot $pair[0]
    if (-not (Test-Path -LiteralPath $abs)) { $PreOk = $false; $PreFail = 'L_r2_claim_absent' }
    elseif ((Get-FileSha256 $abs) -ne $pair[1]) { $PreOk = $false; $PreFail = 'L_r2_claim_sha_mismatch' }
  }
}

# M. all D1 claim TEMP/FINAL paths absent (file or directory occupancy).
if ($PreOk) {
  foreach ($rel in @($AuthTemp, $AuthFinal, $AttemptTemp, $AttemptFinal)) {
    if (Test-Occupied $rel) { $PreOk = $false; $PreFail = 'M_claim_path_occupied' }
  }
}

# N. all D1 output TEMP/FINAL paths absent.
if ($PreOk) {
  foreach ($rel in @($EvTemp, $EvFinal, $MfTemp, $MfFinal, $RsTemp, $RsFinal)) {
    if (Test-Occupied $rel) { $PreOk = $false; $PreFail = 'N_output_path_occupied' }
  }
}

# O. D1 evidence directory absent.
if ($PreOk) { if ([System.IO.Directory]::Exists((Join-Path $RepoRoot $EvDir))) { $PreOk = $false; $PreFail = 'O_evidence_directory_present' } }

# P. D1 result absent.
if ($PreOk) { if (Test-Occupied $RsFinal) { $PreOk = $false; $PreFail = 'P_result_present' } }

if (-not $PreOk) {
  Write-Output ('D1_PRECONDITION_FAILURE=' + $PreFail)
  Write-Output 'D1_PRECONDITION_STAGE=before_claim_consumption'
  Write-Output 'D1_CLAIM_CREATED=0'
  Write-Output 'D1_QUERY_EXECUTED=0'
  Write-Output 'D1_OUTPUT_CREATED=0'
  Write-Output 'D1_BUDGET_ROLLBACK_INFERRED=0'
  exit $ExitPrecondition
}

# ============================================================ CLAIM CONSUMPTION
# A successful TEMP CreateNew is the irreversible consumption boundary. The per-stage
# flag is set to 1 only after CreateNew has returned a stream, so a failure report states
# the observed consumption state instead of inferring budget rollback from an exit code.
# The claim files themselves remain the forensic source of consumption state.
$AuthClaimSha = ''
$AttemptClaimSha = ''
$AuthClaimConsumed = 0
$AttemptClaimConsumed = 0

# --- AUTH claim. Claim byte construction is still stage PRE (no CreateNew yet).
$authBytes = New-ClaimBytes $ClaimSchemaAuth $DesignCommit $DesignSpecSha `
  $AcceptedAuthorizationCommit $ExpectedAuthorizationSha256 $ExpectedScriptSha256

$Stage = 'AUTH'
try {
  $authFs = [System.IO.FileStream]::new((Join-Path $RepoRoot $AuthTemp),
              [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
  $AuthClaimConsumed = 1
  try {
    $authFs.Write($authBytes, 0, $authBytes.Length)
    $authFs.Flush($true)
  } finally { $authFs.Dispose() }
  $authBack = [System.IO.File]::ReadAllBytes((Join-Path $RepoRoot $AuthTemp))
  if (-not (Test-BytesEqual $authBack $authBytes)) { throw 'auth_claim_temp_readback_mismatch' }
  [System.IO.File]::Move((Join-Path $RepoRoot $AuthTemp), (Join-Path $RepoRoot $AuthFinal))
  $authBack2 = [System.IO.File]::ReadAllBytes((Join-Path $RepoRoot $AuthFinal))
  if (-not (Test-BytesEqual $authBack2 $authBytes)) { throw 'auth_claim_final_readback_mismatch' }
  $AuthClaimSha = Get-FileSha256 (Join-Path $RepoRoot $AuthFinal)
} catch {
  Write-Output 'D1_AUTHORIZATION_CLAIM_STAGE_FAILED=1'
  if ($AuthClaimConsumed -eq 1) { Write-Output 'D1_AUTHORIZATION_USE=SPENT' }
  else { Write-Output 'D1_AUTHORIZATION_USE=NOT_CONSUMED' }
  Write-Output ('D1_AUTHORIZATION_CLAIM_CONSUMED=' + [string]$AuthClaimConsumed)
  Write-Output ('D1_AUTHORIZATION_CONSUMPTION_ERROR=' + (Get-Text $_.Exception.Message))
  Write-Output 'D1_ATTEMPT_CONSUMED=0'
  Write-Output ('D1_LISTENER_QUERY_STARTED=' + [string]$QueryStarted)
  Write-Output 'D1_BUDGET_ROLLBACK_INFERRED=0'
  Write-Output 'D1_CLAIM_FILES_ARE_FORENSIC_SOURCE=1'
  exit $ExitAuthClaim
}

# --- ATTEMPT claim. Stage ATTEMPT begins after AUTH completion.
$Stage = 'ATTEMPT'
$attemptBytes = New-ClaimBytes $ClaimSchemaAttempt $DesignCommit $DesignSpecSha `
  $AcceptedAuthorizationCommit $ExpectedAuthorizationSha256 $ExpectedScriptSha256

try {
  $attemptFs = [System.IO.FileStream]::new((Join-Path $RepoRoot $AttemptTemp),
                 [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
  $AttemptClaimConsumed = 1
  try {
    $attemptFs.Write($attemptBytes, 0, $attemptBytes.Length)
    $attemptFs.Flush($true)
  } finally { $attemptFs.Dispose() }
  $attemptBack = [System.IO.File]::ReadAllBytes((Join-Path $RepoRoot $AttemptTemp))
  if (-not (Test-BytesEqual $attemptBack $attemptBytes)) { throw 'attempt_claim_temp_readback_mismatch' }
  [System.IO.File]::Move((Join-Path $RepoRoot $AttemptTemp), (Join-Path $RepoRoot $AttemptFinal))
  $attemptBack2 = [System.IO.File]::ReadAllBytes((Join-Path $RepoRoot $AttemptFinal))
  if (-not (Test-BytesEqual $attemptBack2 $attemptBytes)) { throw 'attempt_claim_final_readback_mismatch' }
  $AttemptClaimSha = Get-FileSha256 (Join-Path $RepoRoot $AttemptFinal)
} catch {
  Write-Output 'D1_ATTEMPT_CLAIM_STAGE_FAILED=1'
  Write-Output 'D1_AUTHORIZATION_USE=SPENT'
  Write-Output ('D1_AUTHORIZATION_CLAIM_SHA256=' + $AuthClaimSha)
  if ($AttemptClaimConsumed -eq 1) { Write-Output 'D1_DIAGNOSTIC_ATTEMPT=SPENT' }
  else { Write-Output 'D1_DIAGNOSTIC_ATTEMPT=NOT_CONSUMED' }
  Write-Output ('D1_ATTEMPT_CLAIM_CONSUMED=' + [string]$AttemptClaimConsumed)
  Write-Output ('D1_ATTEMPT_CONSUMPTION_ERROR=' + (Get-Text $_.Exception.Message))
  Write-Output ('D1_LISTENER_QUERY_STARTED=' + [string]$QueryStarted)
  Write-Output 'D1_BUDGET_ROLLBACK_INFERRED=0'
  Write-Output 'D1_CLAIM_FILES_ARE_FORENSIC_SOURCE=1'
  exit $ExitAttemptClaim
}

# ============================================================== EXECUTION PHASE
# Stage HARNESS. Both budgets are now irreversibly SPENT.
# Order: post-consumption directory occupancy gate -> evidence-directory creation ->
#        command availability -> zero-or-one listener query -> evidence byte construction
#        -> evidence publication -> manifest publication -> result publication -> STOP.
$Stage = 'HARNESS'
$HarnessFailure = ''
$EvDirAbs = Join-Path $RepoRoot $EvDir

$ListenerQueryInvocations = 0
$QueryOutcome = 'DIAGNOSTIC_HARNESS_INVALID'
$Rows = @()
$RowCount = 0
$TerminatingError = $null
$ErrorRecords = @()
$CmdAvailability = 'UNAVAILABLE'
$CmdName = ''
$CmdType = ''
$CmdSource = ''
$CmdVersion = ''
$CmdModule = ''
$Started = ''
$Finished = ''
$Evidence = $null

# Failure report shared by the two post-consumption directory controls below.
function Write-DirectoryControlFailure([string]$reason) {
  Write-Output ('D1_POST_CONSUMPTION_DIRECTORY_CONTROL=' + $reason)
  Write-Output 'D1_EVIDENCE_DIRECTORY_CREATED=0'
  Write-Output 'D1_DIRECTORY_REUSE_ATTEMPTED=0'
  Write-Output 'D1_DIRECTORY_DELETED=0'
  Write-Output 'D1_CLEANUP_ATTEMPTED=0'
  Write-Output 'D1_PUBLISHED=0'
  Write-Output 'D1_LISTENER_QUERY_INVOCATIONS=0'
  Write-Output 'D1_RETRY_AUTHORIZED=0'
  Write-Output 'D1_SECOND_QUERY_AUTHORIZED=0'
  Write-Output 'D1_AUTHORIZATION_USE=SPENT'
  Write-Output 'D1_DIAGNOSTIC_ATTEMPT=SPENT'
  Write-Output 'D1_BUDGET_ROLLBACK_INFERRED=0'
}

try {
  # --- P2: post-consumption directory occupancy gate.
  # Evaluated AFTER both claims are consumed and IMMEDIATELY BEFORE evidence-directory
  # creation, so a directory that appeared between the precondition check and this point
  # can no longer be silently reused. Occupancy means a FILE or a DIRECTORY at that path.
  if ([System.IO.File]::Exists($EvDirAbs) -or [System.IO.Directory]::Exists($EvDirAbs)) {
    Write-DirectoryControlFailure 'DIRECTORY_OCCUPIED_FAIL_CLOSED'
    exit $ExitHarness
  }
  Write-Output 'D1_POST_CONSUMPTION_DIRECTORY_GATE=UNOCCUPIED'

  # --- Evidence-directory creation. Failure is terminal: exit 40, no retry, no cleanup,
  #     no reuse and no fall-through into command availability or the listener query.
  try {
    [void][System.IO.Directory]::CreateDirectory($EvDirAbs)
  } catch {
    Write-DirectoryControlFailure ('DIRECTORY_CREATION_THREW_' + (Get-Text $_.Exception.Message))
    exit $ExitHarness
  }
  if (-not [System.IO.Directory]::Exists($EvDirAbs)) {
    Write-DirectoryControlFailure 'DIRECTORY_CREATION_NOT_OBSERVED'
    exit $ExitHarness
  }
  Write-Output 'D1_EVIDENCE_DIRECTORY_CREATED=1'

  $Started = Get-UtcStamp

  # --- Command availability: narrow inspection only, NOT the listener query, no inventory.
  $cmdInfo = Get-Command -Name 'Get-NetTCPConnection' -ErrorAction SilentlyContinue
  if ($null -ne $cmdInfo) {
    $CmdAvailability = 'AVAILABLE'
    $CmdName = Get-Text $cmdInfo.Name
    $CmdType = Get-Text $cmdInfo.CommandType
    $CmdSource = Get-Text $cmdInfo.Source
    $CmdVersion = Get-Text $cmdInfo.Version
    $CmdModule = Get-Text $cmdInfo.ModuleName
  }

  if ($CmdAvailability -eq 'UNAVAILABLE') {
    # Accepted COMMAND_UNAVAILABLE representation: no listener query occurs.
    $QueryOutcome = 'COMMAND_UNAVAILABLE'
    $ListenerQueryInvocations = 0
    $Rows = @()
    $RowCount = 0
    $TerminatingError = $null
    $ErrorRecords = @()
  } else {
    # The single, exact, one-shot listener query. There is exactly one such site in this file.
    $qerr = @()
    $TerminatingRecord = $null
    $Rows = @()
    $QueryStarted = 1
    try {
      $Rows = @(
        Get-NetTCPConnection `
          -LocalAddress '127.0.0.1' `
          -LocalPort 4096 `
          -State Listen `
          -ErrorAction SilentlyContinue `
          -ErrorVariable qerr
      )
    } catch {
      $TerminatingRecord = $_
    }
    $ListenerQueryInvocations = 1

    $qerrList = @()
    if ($null -ne $qerr) { $qerrList = @($qerr) }
    # RAW pre-suppression qerr state. This count alone drives query_outcome classification;
    # C2 Option B suppression never changes the classifier input.
    $qerrRawCount = $qerrList.Count
    $qerrNormalized = @()
    foreach ($q in $qerrList) { $qerrNormalized += (New-ErrorRecordObject $q 'ERROR_VARIABLE') }

    # ---------------------------------------------------------------- C2 OPTION B
    # OWNER-SELECTED ACCEPTED POLICY: NORMALIZED TERMINATING-DUPLICATE SUPPRESSION.
    # Normalization happens BEFORE comparison. Eligibility requires (a) a terminating
    # catch to have occurred, (b) at least one qerr record, and (c) the candidate being
    # the FINAL observed qerr record. Suppression happens if and only if all 14 payload
    # fields match ordinally. Exactly one record can be suppressed, at most once per
    # execution. All earlier qerr records are retained unconditionally, even when their
    # payload is identical, and no qerr-to-qerr deduplication is performed. Surviving
    # order is preserved. Payload equality is suppression ELIGIBILITY ONLY: it is not
    # proof that the two records are the same underlying PowerShell event, and no such
    # stronger causal claim is made anywhere.
    # There is deliberately NO suppression flag, NO duplicate flag, NO overlap flag and
    # NO raw-count field in the published evidence (top-level closure stays 19/19).
    $publishedErrorRecords = $qerrNormalized

    if ($null -ne $TerminatingRecord) {
      $termNorm = New-ErrorRecordObject $TerminatingRecord 'TERMINATING_EXCEPTION'
      if ($qerrNormalized.Count -gt 0) {
        $lastIndex = $qerrNormalized.Count - 1
        if (Test-RecordPayloadEqual $qerrNormalized[$lastIndex] $termNorm) {
          $surviving = @()
          for ($i = 0; $i -lt $lastIndex; $i++) { $surviving += $qerrNormalized[$i] }
          $publishedErrorRecords = $surviving
        }
      }
      $TerminatingError = $termNorm
      $ErrorRecords = $publishedErrorRecords
      $QueryOutcome = 'TERMINATING_EXCEPTION'
      $Rows = @()
      $RowCount = 0
    } else {
      $TerminatingError = $null
      $ErrorRecords = $publishedErrorRecords
      $RowCount = @($Rows).Count
      if ($qerrRawCount -gt 0 -and $RowCount -eq 0) { $QueryOutcome = 'ERROR_RECORDS_ZERO_ROWS' }
      elseif ($qerrRawCount -gt 0 -and $RowCount -gt 0) { $QueryOutcome = 'ERROR_RECORDS_WITH_ROWS' }
      elseif ($qerrRawCount -eq 0 -and $RowCount -eq 0) { $QueryOutcome = 'ZERO_ROWS' }
      elseif ($qerrRawCount -eq 0 -and $RowCount -eq 1) { $QueryOutcome = 'ONE_ROW' }
      elseif ($qerrRawCount -eq 0 -and $RowCount -gt 1) { $QueryOutcome = 'MULTIPLE_ROWS' }
      else { $QueryOutcome = 'DIAGNOSTIC_HARNESS_INVALID' }
    }
  }

  $Finished = Get-UtcStamp

  $RowObjects = @()
  foreach ($r in @($Rows)) { $RowObjects += (Get-ListenerRow $r) }

  $Evidence = [ordered]@{
    schema_version                       = $SchemaVersion
    source_authoritative_bookkeeping_commit = $SourceBookkeepingCommit
    source_r2_evidence_sha256            = $SourceR2EvidenceSha
    source_r2_result_sha256              = $SourceR2ResultSha
    execution_started_at                 = $Started
    execution_finished_at                = $Finished
    diagnostic_mode                      = $DiagnosticMode
    endpoint                             = $EndpointUri
    configured_base_url                  = $Configured
    powershell_environment               = [ordered]@{
      PSEdition = Get-Text $PSVersionTable.PSEdition
      PSVersion = Get-Text $PSVersionTable.PSVersion
      Platform  = Get-Text $PSVersionTable.Platform
      OS        = Get-Text $PSVersionTable.OS
    }
    command_metadata                     = [ordered]@{
      Name         = $CmdName
      CommandType  = $CmdType
      Source       = $CmdSource
      Version      = $CmdVersion
      ModuleName   = $CmdModule
      availability = $CmdAvailability
    }
    query                                = [ordered]@{
      local_address        = '127.0.0.1'
      local_port           = 4096
      state                = 'Listen'
      error_action         = 'SilentlyContinue'
      error_variable       = 'qerr'
      query_invocation_count = $ListenerQueryInvocations
    }
    query_outcome                        = $QueryOutcome
    row_count                            = [int]$RowCount
    rows                                 = @($RowObjects)
    terminating_error                    = $TerminatingError
    error_records                        = @($ErrorRecords)
    non_claims                           = @($NonClaims)
    activity_counters                    = [ordered]@{
      listener_query_invocations = [int]$ListenerQueryInvocations
      process_queries            = 0
      target_executable_hashes   = 0
      opencode_starts            = 0
      http_requests              = 0
      provider_model_calls       = 0
      retries                    = 0
      fallbacks                  = 0
    }
  }
} catch {
  # A harness/control failure after consumption. Nothing is published; the control state
  # becomes a D1 operational harness failure, which is NOT a query_outcome value.
  $HarnessFailure = Get-Text $_.Exception.Message
}

if ($HarnessFailure -ne '') {
  Write-Output ('D1_OPERATIONAL_HARNESS_FAILURE=' + $HarnessFailure)
  Write-Output 'D1_PUBLISHED=0'
  Write-Output 'D1_RETRY_AUTHORIZED=0'
  Write-Output 'D1_SECOND_QUERY_AUTHORIZED=0'
  Write-Output 'D1_AUTHORIZATION_USE=SPENT'
  Write-Output 'D1_DIAGNOSTIC_ATTEMPT=SPENT'
  Write-Output 'D1_BUDGET_ROLLBACK_INFERRED=0'
  exit $ExitHarness
}

# ================================================================== PUBLICATION
# Stage PUBLICATION. Order: evidence -> manifest -> result. Atomic, no-overwrite, no retry.
$Stage = 'PUBLICATION'
$pubOk = $true
$pubStage = 'evidence_serialization'
$evSha = ''
$mfSha = ''
try {
  $enc = [System.Text.UTF8Encoding]::new($false)
  $evJson = $Evidence | ConvertTo-Json -Depth $JsonDepth -Compress
  $evBody = $evJson.Replace("`r`n", "`n").Replace("`r", "`n")
  if (-not $evBody.EndsWith("`n")) { $evBody = $evBody + "`n" }
  $evBytes = $enc.GetBytes($evBody)

  $pubStage = 'evidence'
  if (Test-Occupied $EvTemp -or Test-Occupied $EvFinal) { throw 'evidence_output_occupied' }
  if (-not (Write-AtomicFile $EvTemp $EvFinal $evBytes)) { throw 'evidence_write_or_readback_failed' }
  $evSha = Get-FileSha256 (Join-Path $RepoRoot $EvFinal)

  $pubStage = 'manifest'
  if (Test-Occupied $MfTemp -or Test-Occupied $MfFinal) { throw 'manifest_output_occupied' }
  # Manifest binds the evidence file only; exact one-line format; the manifest never self-lists.
  $mfText = $evSha + '  ' + $EvFinal + "`n"
  $mfBytes = $enc.GetBytes($mfText)
  if (-not (Write-AtomicFile $MfTemp $MfFinal $mfBytes)) { throw 'manifest_write_or_readback_failed' }
  $mfSha = Get-FileSha256 (Join-Path $RepoRoot $MfFinal)

  $pubStage = 'result'
  if (Test-Occupied $RsTemp -or Test-Occupied $RsFinal) { throw 'result_output_occupied' }
  $rl = [System.Collections.Generic.List[string]]::new()
  $rl.Add('# DevRelay v0.3-E - ETB QUERY_EXCEPTION DIAGNOSTIC D1 - diagnostic result (candidate)')
  $rl.Add('')
  $rl.Add('result_schema_version=' + $SchemaVersion)
  $rl.Add('diagnostic_d1_design_commit=' + $DesignCommit)
  $rl.Add('diagnostic_d1_spec_sha256=' + $DesignSpecSha)
  $rl.Add('diagnostic_d1_authorization_commit=' + $AcceptedAuthorizationCommit)
  $rl.Add('diagnostic_d1_authorization_sha256=' + $ExpectedAuthorizationSha256)
  $rl.Add('diagnostic_d1_script_sha256=' + $ExpectedScriptSha256)
  $rl.Add('source_authoritative_bookkeeping_commit=' + $SourceBookkeepingCommit)
  $rl.Add('query_diagnostic_evidence_sha256=' + $evSha)
  $rl.Add('query_diagnostic_manifest_sha256=' + $mfSha)
  $rl.Add('query_outcome=' + $QueryOutcome)
  $rl.Add('listener_query_invocations=' + [string]$ListenerQueryInvocations)
  $rl.Add('authorization_claim_state=CONSUMED')
  $rl.Add('attempt_claim_state=CONSUMED')
  $rl.Add('diagnostic_authority_state=CANDIDATE / REQUIRES INDEPENDENT RESULT REVIEW')
  $rl.Add('authoritative_etb_semantic_result=ETB_UNSATISFIED')
  $rl.Add('')
  $rl.Add('Non-claims:')
  foreach ($nc in $NonClaims) { $rl.Add('- ' + $nc) }
  $rl.Add('')
  $rlText = ($rl.ToArray() -join "`n") + "`n"
  $rsBytes = $enc.GetBytes($rlText)
  if (-not (Write-AtomicFile $RsTemp $RsFinal $rsBytes)) { throw 'result_write_or_readback_failed' }
} catch {
  $pubOk = $false
}

if (-not $pubOk) {
  Write-Output ('D1_PUBLICATION_INCOMPLETE_STAGE=' + $pubStage)
  Write-Output 'D1_PUBLICATION_INCOMPLETE=1'
  Write-Output 'D1_RETRY_AUTHORIZED=0'
  Write-Output 'D1_SECOND_QUERY_AUTHORIZED=0'
  Write-Output 'D1_AUTHORIZATION_USE=SPENT'
  Write-Output 'D1_DIAGNOSTIC_ATTEMPT=SPENT'
  Write-Output 'D1_BUDGET_ROLLBACK_INFERRED=0'
  exit $ExitPublication
}

Write-Output ('D1_QUERY_OUTCOME=' + $QueryOutcome)
Write-Output ('D1_LISTENER_QUERY_INVOCATIONS=' + [string]$ListenerQueryInvocations)
Write-Output ('D1_EVIDENCE_SHA256=' + $evSha)
Write-Output ('D1_MANIFEST_SHA256=' + $mfSha)
Write-Output ('D1_AUTHORIZATION_CLAIM_SHA256=' + $AuthClaimSha)
Write-Output ('D1_ATTEMPT_CLAIM_SHA256=' + $AttemptClaimSha)
Write-Output 'D1_AUTHORIZATION_USE=SPENT'
Write-Output 'D1_DIAGNOSTIC_ATTEMPT=SPENT'
exit $ExitOk
