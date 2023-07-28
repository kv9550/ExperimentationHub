# Use Case for this was to automate uploads to AWS S3 via AWS Transfer Family: SFTP from a Windows Bastion Host
# I realized that someone else might have a similar use case or might need to automate SFTP transfers from Windows and decided to publish the script here
# This is the script to upload files from Windows Server to an AWS SFTP Transfer backed AWS S3 Bucket
# kv | 28/07/2023 | v0.10

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
