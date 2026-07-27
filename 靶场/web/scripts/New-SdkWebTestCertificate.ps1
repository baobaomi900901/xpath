[CmdletBinding()]
param([string] $WorkDir = $env:UIPILOT_SDK_WEB_WORKDIR)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($WorkDir)) { throw 'WorkDir or UIPILOT_SDK_WEB_WORKDIR is required.' }
if (-not [IO.Path]::IsPathRooted($WorkDir)) { throw 'WorkDir must be absolute.' }

$certificateDir = Join-Path ([IO.Path]::GetFullPath($WorkDir)) 'certificate'
New-Item -ItemType Directory -Path $certificateDir -Force | Out-Null
$pfxPath = Join-Path $certificateDir 'sdk-web-test.pfx'
$cerPath = Join-Path $certificateDir 'sdk-web-test.cer'
$passwordPath = Join-Path $certificateDir 'pfx-password.txt'
$pinPath = Join-Path $certificateDir 'spki-pin.txt'

$rsa = [Security.Cryptography.RSA]::Create(2048)
try {
    $subject = [Security.Cryptography.X509Certificates.X500DistinguishedName]::new('CN=sdk-web.test')
    $request = [Security.Cryptography.X509Certificates.CertificateRequest]::new(
        $subject, $rsa, [Security.Cryptography.HashAlgorithmName]::SHA256,
        [Security.Cryptography.RSASignaturePadding]::Pkcs1
    )
    $san = [Security.Cryptography.X509Certificates.SubjectAlternativeNameBuilder]::new()
    $san.AddDnsName('sdk-web.test')
    $san.AddDnsName('sub.sdk-web.test')
    $request.CertificateExtensions.Add($san.Build())
    $request.CertificateExtensions.Add([Security.Cryptography.X509Certificates.X509BasicConstraintsExtension]::new($false, $false, 0, $true))
    $request.CertificateExtensions.Add([Security.Cryptography.X509Certificates.X509KeyUsageExtension]::new([Security.Cryptography.X509Certificates.X509KeyUsageFlags]::DigitalSignature, $true))
    $certificate = $request.CreateSelfSigned([DateTimeOffset]::UtcNow.AddMinutes(-5), [DateTimeOffset]::UtcNow.AddDays(7))
    try {
        $passwordBytes = [byte[]]::new(32)
        $random = [Security.Cryptography.RandomNumberGenerator]::Create()
        try { $random.GetBytes($passwordBytes) } finally { $random.Dispose() }
        $password = [Convert]::ToBase64String($passwordBytes)
        [IO.File]::WriteAllBytes($pfxPath, $certificate.Export([Security.Cryptography.X509Certificates.X509ContentType]::Pfx, $password))
        [IO.File]::WriteAllBytes($cerPath, $certificate.Export([Security.Cryptography.X509Certificates.X509ContentType]::Cert))
        [IO.File]::WriteAllText($passwordPath, $password, [Text.UTF8Encoding]::new($false))
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
        & icacls.exe $passwordPath /inheritance:r /grant:r "${identity}:(R,W,D)" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Failed to restrict the PFX password file ACL.' }
        $env:UIPILOT_SDK_WEB_CERT_CER_PATH = $cerPath
        $nodeScript = @(
            "const { X509Certificate, createHash } = require('node:crypto');",
            "const fs = require('node:fs');",
            "const certificate = new X509Certificate(fs.readFileSync(process.env.UIPILOT_SDK_WEB_CERT_CER_PATH));",
            "const spkiDer = certificate.publicKey.export({ type: 'spki', format: 'der' });",
            "process.stdout.write(createHash('sha256').update(spkiDer).digest('base64'));"
        ) -join "`n"
        $pin = (& node.exe -e $nodeScript)
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($pin)) { throw 'Failed to compute the certificate SPKI pin with Node.js.' }
        [IO.File]::WriteAllText($pinPath, $pin, [Text.UTF8Encoding]::new($false))
        [Console]::Out.WriteLine($pin)
    }
    finally { $certificate.Dispose() }
}
finally {
    $rsa.Dispose()
    Remove-Item Env:UIPILOT_SDK_WEB_CERT_CER_PATH -ErrorAction SilentlyContinue
}

