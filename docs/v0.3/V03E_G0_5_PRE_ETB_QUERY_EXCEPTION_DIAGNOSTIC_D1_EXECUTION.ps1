# DevRelay v0.3-E - G0.5-PRE / SIC - ETB QUERY_EXCEPTION DIAGNOSTIC D1 (execution script)
#
# ASCII-ONLY SOURCE. Every byte of this file MUST be <= 0x7F.
#
# STATUS OF THIS FILE: tracked design/implementation SOURCE ONLY.
#   D1 IMPLEMENTATION = CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED.
#   This file MUST NOT be executed until an independently accepted execution authorization
#   and its independently confirmed bookkeeping exist. This construction round does not run it.
#
# AUTHORITATIVE DESIGN (C1-clarified, accepted):
#   diagnostic_d1_design_commit = b8f8a67beac154894e496aaa601fa0a4cd4e9905
#   diagnostic_d1_spec_sha256   = 29f0f9cc1632f2f344f5cb4e01d25a832ba9acc78caedbdd43861b7d68ac4154
#
# This script is the future execution entrypoint. It is NOT an ETB semantic attempt:
# no observation produced by it may become or replace AUTHORITATIVE ETB SEMANTIC RESULT.
#
# Self-integrity: this script does NOT embed its own commit id or its own expected SHA-256.
# Those arrive as mandatory parameters and are frozen only after independent review and
# acceptance bookkeeping.

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$AcceptedAuthorizationCommit,
  [Parameter(Mandatory = $true)][string]$ExpectedAuthorizationSha256,
  [Parameter(Mandatory = $true)][string]$ExpectedScriptSha256
)

$ErrorActionPreference = 'Stop'

# Repository root is derived deterministically from the tracked script location:
# this file lives at <repo>/docs/v0.3/, so the grandparent of $PSScriptRoot is <repo>.
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location -LiteralPath $RepoRoot
$Inv = [System.Globalization.CultureInfo]::InvariantCulture

# ------------------------------------------------------------------ exit codes
$ExitOk            = 0
$ExitPrecondition  = 10
$ExitAuthClaim     = 20
$ExitAttemptClaim  = 30
$ExitHarness       = 40
$ExitPublication   = 50

# ------------------------------------------------------- fixed design constants
$SchemaVersion = 'devrelay-etb-query-diagnostic-d1-v1'
$DiagnosticMode = 'QUERY_EXCEPTION_DIAGNOSTIC_D1'
$EndpointUri = 'http://127.0.0.1:4096'

$DesignCommit = 'b8f8a67beac154894e496aaa601fa0a4cd4e9905'
$DesignSpecSha = '29f0f9cc1632f2f344f5cb4e01d25a832ba9acc78caedbdd43861b7d68ac4154'

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
  $abs = Join-Path $RepoRoot $relPath
  return ([System.IO.File]::Exists($abs) -or [System.IO.Directory]::Exists($abs))
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

function Get-GitBlobText([string]$commit, [string]$relPath) {
  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = 'git'
  $psi.Arguments = '-C "' + $RepoRoot + '" cat-file blob ' + $commit + ':' + $relPath
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
  $p = [System.Diagnostics.Process]::Start($psi)
  $out = $p.StandardOutput.ReadToEnd()
  $p.WaitForExit()
  if ($p.ExitCode -ne 0) { return $null }
  return $out
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
  # Compare the 14 payload fields (all except `source`), in the accepted order.
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
  if ($back.Length -ne $bytes.Length) { return $false }
  for ($i = 0; $i -lt $bytes.Length; $i++) { if ($back[$i] -ne $bytes[$i]) { return $false } }
  [System.IO.File]::Move($absTemp, $absFinal)
  $back2 = [System.IO.File]::ReadAllBytes($absFinal)
  if ($back2.Length -ne $bytes.Length) { return $false }
  for ($i = 0; $i -lt $bytes.Length; $i++) { if ($back2[$i] -ne $bytes[$i]) { return $false } }
  return $true
}

function Get-ListenerRow([object]$row) {
  # Only the accepted row fields, frozen order. LocalPort / OwningProcess: observed integer or null.
  # LocalAddress / State: observed string or "".
  $addr = ''
  $state = ''
  $port = $null
  $pid = $null
  if ($null -ne $row.LocalAddress) { $addr = [string]$row.LocalAddress }
  if ($null -ne $row.State) { $state = [string]$row.State }
  if ($null -ne $row.LocalPort) { $port = [int]$row.LocalPort }
  if ($null -ne $row.OwningProcess) { $pid = [int]$row.OwningProcess }
  return [ordered]@{
    LocalAddress  = $addr
    LocalPort     = $port
    State         = $state
    OwningProcess = $pid
  }
}

# ================================================================== PRECONDITIONS
# Every precondition A-P is evaluated BEFORE any claim consumption.
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
  exit $ExitPrecondition
}

# ============================================================ CLAIM CONSUMPTION
# The successful TEMP CreateNew of each claim is the irreversible consumption boundary.
$AuthClaimSha = ''
$AttemptClaimSha = ''

$authBytes = New-ClaimBytes $ClaimSchemaAuth $DesignCommit $DesignSpecSha `
  $AcceptedAuthorizationCommit $ExpectedAuthorizationSha256 $ExpectedScriptSha256

try {
  if (-not (Write-AtomicFile $AuthTemp $AuthFinal $authBytes)) { throw 'auth_claim_write_or_readback_failed' }
} catch {
  Write-Output 'D1_AUTHORIZATION_USE=SPENT'
  Write-Output ('D1_AUTHORIZATION_CONSUMPTION_ERROR=' + $_.Exception.Message)
  Write-Output 'D1_ATTEMPT_CONSUMED=0'
  Write-Output 'D1_QUERY_EXECUTED=0'
  exit $ExitAuthClaim
}
$AuthClaimSha = Get-FileSha256 (Join-Path $RepoRoot $AuthFinal)

$attemptBytes = New-ClaimBytes $ClaimSchemaAttempt $DesignCommit $DesignSpecSha `
  $AcceptedAuthorizationCommit $ExpectedAuthorizationSha256 $ExpectedScriptSha256

try {
  if (-not (Write-AtomicFile $AttemptTemp $AttemptFinal $attemptBytes)) { throw 'attempt_claim_write_or_readback_failed' }
} catch {
  Write-Output 'D1_AUTHORIZATION_USE=SPENT'
  Write-Output ('D1_AUTHORIZATION_CLAIM_SHA256=' + $AuthClaimSha)
  Write-Output 'D1_DIAGNOSTIC_ATTEMPT=SPENT'
  Write-Output ('D1_ATTEMPT_CONSUMPTION_ERROR=' + $_.Exception.Message)
  Write-Output 'D1_QUERY_EXECUTED=0'
  exit $ExitAttemptClaim
}
$AttemptClaimSha = Get-FileSha256 (Join-Path $RepoRoot $AttemptFinal)

# ============================================================== EXECUTION PHASE
# Order: evidence-directory creation -> command availability -> zero-or-one listener query
#        -> evidence publication -> manifest publication -> result publication -> STOP.
$Started = Get-UtcStamp
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
$OperationalFailure = ''

try {
  # Executing this script is forbidden until a separately accepted authorization exists.
  # The directory is created only AFTER both claims are consumed.
  [void][System.IO.Directory]::CreateDirectory((Join-Path $RepoRoot $EvDir))

  # Command availability: narrow inspection only, NOT the listener query, no inventory.
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
    $qerrCount = $qerrList.Count
    $normalized = @()
    foreach ($q in $qerrList) { $normalized += (New-ErrorRecordObject $q 'ERROR_VARIABLE') }

    if ($null -ne $TerminatingRecord) {
      $termNorm = New-ErrorRecordObject $TerminatingRecord 'TERMINATING_EXCEPTION'
      # Deterministic no-duplication: if and only if the FINAL qerr entry has the same normalized
      # 14 payload fields as the terminating record (excluding `source`), drop exactly that one
      # final qerr entry. Retain all earlier entries, even if payload-identical. Never remove more
      # than one.
      if ($normalized.Count -gt 0) {
        $lastIndex = $normalized.Count - 1
        if (Test-RecordPayloadEqual $normalized[$lastIndex] $termNorm) {
          $trimmed = @()
          for ($i = 0; $i -lt $lastIndex; $i++) { $trimmed += $normalized[$i] }
          $normalized = $trimmed
        }
      }
      $TerminatingError = $termNorm
      $ErrorRecords = $normalized
      $QueryOutcome = 'TERMINATING_EXCEPTION'
      $Rows = @()
      $RowCount = 0
    } else {
      $TerminatingError = $null
      $ErrorRecords = $normalized
      $RowCount = @($Rows).Count
      if ($qerrCount -gt 0 -and $RowCount -eq 0) { $QueryOutcome = 'ERROR_RECORDS_ZERO_ROWS' }
      elseif ($qerrCount -gt 0 -and $RowCount -gt 0) { $QueryOutcome = 'ERROR_RECORDS_WITH_ROWS' }
      elseif ($qerrCount -eq 0 -and $RowCount -eq 0) { $QueryOutcome = 'ZERO_ROWS' }
      elseif ($qerrCount -eq 0 -and $RowCount -eq 1) { $QueryOutcome = 'ONE_ROW' }
      elseif ($qerrCount -eq 0 -and $RowCount -gt 1) { $QueryOutcome = 'MULTIPLE_ROWS' }
      else { $QueryOutcome = 'DIAGNOSTIC_HARNESS_INVALID' }
    }
  }
} catch {
  # A harness/control failure after consumption. If the closed schema can still be constructed
  # truthfully it is published as DIAGNOSTIC_HARNESS_INVALID; otherwise no evidence record is
  # fabricated and the control state becomes an operational harness/publication failure.
  $QueryOutcome = 'DIAGNOSTIC_HARNESS_INVALID'
  $OperationalFailure = $_.Exception.Message
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

if ($OperationalFailure -ne '') {
  Write-Output ('D1_OPERATIONAL_HARNESS_FAILURE=' + $OperationalFailure)
  Write-Output 'D1_PUBLISHED=0'
  Write-Output 'D1_RETRY_AUTHORIZED=0'
  Write-Output 'D1_AUTHORIZATION_USE=SPENT'
  Write-Output 'D1_DIAGNOSTIC_ATTEMPT=SPENT'
  exit $ExitHarness
}

# ================================================================== PUBLICATION
# Order: evidence -> manifest -> result. Atomic, no-overwrite, no retry.
$enc = [System.Text.UTF8Encoding]::new($false)
$evJson = $Evidence | ConvertTo-Json -Depth $JsonDepth -Compress
$evBody = $evJson.Replace("`r`n", "`n").Replace("`r", "`n")
if (-not $evBody.EndsWith("`n")) { $evBody = $evBody + "`n" }
$evBytes = $enc.GetBytes($evBody)

$pubOk = $true
$pubStage = ''
try {
  if (Test-Occupied $EvTemp -or Test-Occupied $EvFinal) { throw 'evidence_output_occupied' }
  $pubStage = 'evidence'
  if (-not (Write-AtomicFile $EvTemp $EvFinal $evBytes)) { $pubOk = $false }
} catch { $pubOk = $false }

$evSha = ''
if ($pubOk) { $evSha = Get-FileSha256 (Join-Path $RepoRoot $EvFinal) }

$mfBytes = $null
if ($pubOk) {
  try {
    if (Test-Occupied $MfTemp -or Test-Occupied $MfFinal) { throw 'manifest_output_occupied' }
    $pubStage = 'manifest'
    # Manifest binds the evidence file only; exact one-line format; the manifest never self-lists.
    $mfText = $evSha + '  ' + $EvFinal + "`n"
    $mfBytes = $enc.GetBytes($mfText)
    if (-not (Write-AtomicFile $MfTemp $MfFinal $mfBytes)) { $pubOk = $false }
  } catch { $pubOk = $false }
}

$mfSha = ''
if ($pubOk) { $mfSha = Get-FileSha256 (Join-Path $RepoRoot $MfFinal) }

if ($pubOk) {
  try {
    if (Test-Occupied $RsTemp -or Test-Occupied $RsFinal) { throw 'result_output_occupied' }
    $pubStage = 'result'
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
    if (-not (Write-AtomicFile $RsTemp $RsFinal $rsBytes)) { $pubOk = $false }
  } catch { $pubOk = $false }
}

if (-not $pubOk) {
  Write-Output ('D1_PUBLICATION_INCOMPLETE_STAGE=' + $pubStage)
  Write-Output 'D1_PUBLICATION_INCOMPLETE=1'
  Write-Output 'D1_RETRY_AUTHORIZED=0'
  Write-Output 'D1_SECOND_QUERY_AUTHORIZED=0'
  Write-Output 'D1_AUTHORIZATION_USE=SPENT'
  Write-Output 'D1_DIAGNOSTIC_ATTEMPT=SPENT'
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
