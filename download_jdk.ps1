$jdkUrl = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.10%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.10_7.zip"
$outZip = "$env:TEMP\jdk17.zip"
$destDir = "$env:USERPROFILE\.jdks"

New-Item -ItemType Directory -Force -Path $destDir | Out-Null
Write-Host "Downloading JDK 17 Zip..."
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
(New-Object System.Net.WebClient).DownloadFile($jdkUrl, $outZip)
Write-Host "Extracting JDK 17..."
Expand-Archive -Path $outZip -DestinationPath $destDir -Force
Write-Host "JDK 17 Extracted Successfully!"
