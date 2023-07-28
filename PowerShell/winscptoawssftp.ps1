# This is the script to upload files from the server to the SFTP Transfer backed S3
# Load WinSCP .NET assembly
Add-Type -Path "C:\Program Files (x86)\WinSCP\WinSCPnet.dll"

# Set up session options
$sessionOptions = New-Object WinSCP.SessionOptions -Property @{
    Protocol = [WinSCP.Protocol]::Sftp
    HostName = ""
    UserName = ""
    SshPrivateKeyPath = ""
    SshHostKeyFingerprint = "ssh-rsa 2048 MD5 Fingerprint"
}

# Check if the private key file exists
if (-not (Test-Path -Path $sessionOptions.SshPrivateKeyPath)) {
    Write-Error "Private key file not found at the specified path"
    return
}

$session = New-Object WinSCP.Session

try {
    # Connect
    $session.Open($sessionOptions)

    # Set up transfer options
    $transferOptions = New-Object WinSCP.TransferOptions
    $transferOptions.TransferMode = [WinSCP.TransferMode]::Binary
    $transferOptions.PreserveTimestamp = $False

    # Upload files
    $transferResult = $session.PutFiles("C:\Path\File", "/uploadfolder/", $False, $transferOptions)

    # Check for successful upload
    $transferResult.Check()

    # Print results
    foreach ($transfer in $transferResult.Transfers) {
        Write-Host "Upload of $($transfer.FileName) succeeded"
    }
}
catch {
    Write-Error "Error occurred during file transfer: $_"
}
finally {
    # Disconnect, clean up
    $session.Dispose()
}
