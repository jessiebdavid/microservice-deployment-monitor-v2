$p = "src\App.tsx"
$s = Get-Content $p -Raw

# 1. Import getDeploymentStats
if ($s -notmatch "getDeploymentStats") {
    $s = $s -replace "(\s*getDeploymentValidations,)", '$1' + "`r`n  getDeploymentStats,"
}

# 2. Add deploymentStats state
if ($s -notmatch "const \[deploymentStats, setDeploymentStats\]") {
    $pattern = '(const \[latestValidations, setLatestValidations\]\s*=\s*useState<ValidationResult\[\]>\(\[\]\))'
    $replacement = '$1' + "`r`n`r`n  const [deploymentStats, setDeploymentStats] = useState<{" + "`r`n" +
        "    total: number" + "`r`n" +
        "    validating: number" + "`r`n" +
        "    success: number" + "`r`n" +
        "    failed: number" + "`r`n" +
        "    pending: number" + "`r`n" +
        "  } | null>(null)"
    $s = [regex]::Replace($s, $pattern, $replacement, 1)
}

# 3. Add stats refresh function
if ($s -notmatch "const refreshDeploymentStats = async") {
    $marker = "  const handleDeploymentComplete = ("
    $insert = @"

  const refreshDeploymentStats = async () => {
    try {
      const stats = await getDeploymentStats()
      setDeploymentStats(stats)
    } catch {
      // Keep the Overview usable if statistics are temporarily unavailable.
    }
  }

  useEffect(() => {
    void refreshDeploymentStats()
  }, [])

"@
    $s = $s.Replace($marker, $insert + $marker)
}

# 4. Refresh stats after a new deployment
if ($s -notmatch "void refreshDeploymentStats\(\)" -or
    ([regex]::Matches($s, "void refreshDeploymentStats\(\)").Count -lt 2)) {

    $pattern = "(window\.localStorage\.setItem\(\s*['""]deployguard\.latestValidations['""],\s*JSON\.stringify\(validations\),\s*\))"
    if ($s -match $pattern) {
        $s = [regex]::Replace(
            $s,
            $pattern,
            '$1' + "`r`n`r`n    void refreshDeploymentStats()",
            1
        )
    }
}

# 5. Pass stats into OverviewPage
if ($s -notmatch "deploymentStats=\{deploymentStats\}") {
    $pattern = '(<OverviewPage\s*onInitialize=\{\(\) => switchPage\(''Deployments''\)\}\s*latestDeployment=\{latestDeployment\})'
    $replacement = '$1' + "`r`n            deploymentStats={deploymentStats}"
    $s = [regex]::Replace($s, $pattern, $replacement, 1)
}

# 6. Add deploymentStats to OverviewPage props
if ($s -notmatch "deploymentStats: \{") {
    $pattern = '(latestDeployment: Deployment \| null\s*\r?\n\})'
    $replacement = @"
latestDeployment: Deployment | null
  deploymentStats: {
    total: number
    validating: number
    success: number
    failed: number
    pending: number
  } | null
}
"@
    $s = [regex]::Replace($s, $pattern, $replacement, 1)
}

# 7. Replace session counters with real backend stats
$old = @"
  const deployments = latestDeployment ? '1' : '0'
  const passed = latestDeployment?.status === 'SUCCESS' ? '1' : '0'
  const failed = latestDeployment?.status === 'FAILED' ? '1' : '0'
  const running =
    latestDeployment &&
    (latestDeployment.status === 'PENDING' ||
      latestDeployment.status === 'VALIDATING')
      ? '1'
      : '0'
"@

$new = @"
  const deployments = String(deploymentStats?.total ?? 0)
  const passed = String(deploymentStats?.success ?? 0)
  const failed = String(deploymentStats?.failed ?? 0)
  const running = String(
    (deploymentStats?.validating ?? 0) +
      (deploymentStats?.pending ?? 0),
  )
"@

if ($s.Contains($old)) {
    $s = $s.Replace($old, $new)
}

# 8. Rename metric
$s = $s.Replace(
    'label="Session deployments"',
    'label="Total deployments"'
)

# Write UTF-8 without BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText(
    (Resolve-Path $p),
    $s,
    $utf8NoBom
)

Write-Host ""
Write-Host "Overview statistics patch applied successfully." -ForegroundColor Green
