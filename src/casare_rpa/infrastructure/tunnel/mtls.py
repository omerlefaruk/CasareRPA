"""
mTLS (Mutual TLS) Configuration and Certificate Management.

Provides secure mutual authentication between on-prem robots and cloud control plane.
"""

import ssl
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
from enum import Enum

from loguru import logger

# Optional cryptography for certificate generation
try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, ec
    from cryptography.hazmat.backends import default_backend

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class CertificateType(Enum):
    """Types of certificates."""

    CA = "ca"
    SERVER = "server"
    CLIENT = "client"


@dataclass
class MTLSConfig:
    """
    Configuration for mTLS authentication.

    Attributes:
        ca_cert_path: Path to CA certificate (PEM)
        client_cert_path: Path to client certificate (PEM)
        client_key_path: Path to client private key (PEM)
        verify_server: Whether to verify server certificate
        check_hostname: Whether to check server hostname
        ciphers: Allowed TLS ciphers (None for default)
        minimum_version: Minimum TLS version
    """

    ca_cert_path: Path
    client_cert_path: Path
    client_key_path: Path
    verify_server: bool = True
    check_hostname: bool = True
    ciphers: Optional[str] = None
    minimum_version: ssl.TLSVersion = ssl.TLSVersion.TLSv1_2

    def create_ssl_context(self) -> ssl.SSLContext:
        """
        Create SSL context configured for mTLS.

        Returns:
            Configured SSLContext for client-side mTLS

        Raises:
            FileNotFoundError: If certificate files don't exist
            ssl.SSLError: If certificate loading fails
        """
        # Verify files exist
        for path, name in [
            (self.ca_cert_path, "CA certificate"),
            (self.client_cert_path, "Client certificate"),
            (self.client_key_path, "Client key"),
        ]:
            if not path.exists():
                raise FileNotFoundError(f"{name} not found: {path}")

        # Create context for client authentication
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.minimum_version = self.minimum_version

        # Load CA certificate for server verification
        context.load_verify_locations(cafile=str(self.ca_cert_path))

        # Load client certificate and key for client authentication
        context.load_cert_chain(
            certfile=str(self.client_cert_path),
            keyfile=str(self.client_key_path),
        )

        # Configure verification
        if self.verify_server:
            context.verify_mode = ssl.CERT_REQUIRED
            context.check_hostname = self.check_hostname
        else:
            context.verify_mode = ssl.CERT_NONE
            context.check_hostname = False
            logger.warning(
                "mTLS: Server verification disabled - NOT RECOMMENDED for production"
            )

        # Set ciphers if specified
        if self.ciphers:
            context.set_ciphers(self.ciphers)

        logger.debug(
            f"mTLS context created: verify={self.verify_server}, "
            f"min_version={self.minimum_version.name}"
        )

        return context


@dataclass
class CertificateInfo:
    """Information about a certificate."""

    subject: Dict[str, str]
    issuer: Dict[str, str]
    serial_number: int
    not_valid_before: datetime
    not_valid_after: datetime
    is_ca: bool
    key_type: str
    key_size: int


class CertificateManager:
    """
    Manages certificates for mTLS authentication.

    Provides:
    - Certificate generation (CA, server, client)
    - Certificate validation
    - Certificate info extraction
    - Expiration monitoring
    """

    def __init__(self, certs_dir: Path):
        """
        Initialize certificate manager.

        Args:
            certs_dir: Directory to store certificates
        """
        self.certs_dir = Path(certs_dir)
        self.certs_dir.mkdir(parents=True, exist_ok=True)

        self._ca_cert: Optional[Path] = None
        self._ca_key: Optional[Path] = None

    def generate_ca(
        self,
        common_name: str = "CasareRPA CA",
        organization: str = "CasareRPA",
        validity_days: int = 3650,  # 10 years
        key_size: int = 4096,
    ) -> tuple[Path, Path]:
        """
        Generate a new Certificate Authority.

        Args:
            common_name: CA common name
            organization: Organization name
            validity_days: Certificate validity in days
            key_size: RSA key size

        Returns:
            Tuple of (cert_path, key_path)

        Raises:
            ImportError: If cryptography library not available
        """
        if not HAS_CRYPTOGRAPHY:
            raise ImportError(
                "cryptography library required for certificate generation. "
                "Install with: pip install cryptography"
            )

        # Generate private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend(),
        )

        # Build certificate
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ]
        )

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=validity_days))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_cert_sign=True,
                    crl_sign=True,
                    key_encipherment=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(key, hashes.SHA256(), default_backend())
        )

        # Save certificate and key
        cert_path = self.certs_dir / "ca.crt"
        key_path = self.certs_dir / "ca.key"

        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(key_path, "wb") as f:
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Restrict key file permissions
        os.chmod(key_path, 0o600)

        self._ca_cert = cert_path
        self._ca_key = key_path

        logger.info(f"CA certificate generated: {cert_path}")
        return cert_path, key_path

    def generate_certificate(
        self,
        cert_type: CertificateType,
        common_name: str,
        organization: str = "CasareRPA",
        validity_days: int = 365,
        key_size: int = 2048,
        san_dns: Optional[list[str]] = None,
        san_ips: Optional[list[str]] = None,
    ) -> tuple[Path, Path]:
        """
        Generate a signed certificate (server or client).

        Args:
            cert_type: Type of certificate (SERVER or CLIENT)
            common_name: Certificate common name
            organization: Organization name
            validity_days: Certificate validity in days
            key_size: RSA key size
            san_dns: Subject Alternative Names (DNS)
            san_ips: Subject Alternative Names (IP addresses)

        Returns:
            Tuple of (cert_path, key_path)

        Raises:
            ValueError: If CA not loaded/generated
            ImportError: If cryptography library not available
        """
        if not HAS_CRYPTOGRAPHY:
            raise ImportError(
                "cryptography library required for certificate generation. "
                "Install with: pip install cryptography"
            )

        if not self._ca_cert or not self._ca_key:
            # Try to load existing CA
            ca_cert_path = self.certs_dir / "ca.crt"
            ca_key_path = self.certs_dir / "ca.key"

            if ca_cert_path.exists() and ca_key_path.exists():
                self._ca_cert = ca_cert_path
                self._ca_key = ca_key_path
            else:
                raise ValueError(
                    "CA certificate not found. Generate CA first with generate_ca()"
                )

        # Load CA certificate and key
        with open(self._ca_cert, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())

        with open(self._ca_key, "rb") as f:
            ca_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )

        # Generate private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend(),
        )

        # Build certificate
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ]
        )

        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_cert.subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=validity_days))
        )

        # Add extensions based on type
        if cert_type == CertificateType.SERVER:
            builder = builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            builder = builder.add_extension(
                x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),
                critical=False,
            )
        elif cert_type == CertificateType.CLIENT:
            builder = builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            builder = builder.add_extension(
                x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]),
                critical=False,
            )

        # Add Subject Alternative Names
        san_list = []
        if san_dns:
            san_list.extend([x509.DNSName(dns) for dns in san_dns])
        if san_ips:
            from ipaddress import ip_address

            san_list.extend([x509.IPAddress(ip_address(ip)) for ip in san_ips])

        if san_list:
            builder = builder.add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False,
            )

        # Sign certificate
        cert = builder.sign(ca_key, hashes.SHA256(), default_backend())

        # Save certificate and key
        safe_name = common_name.replace(" ", "_").replace(".", "_").lower()
        cert_path = self.certs_dir / f"{safe_name}.crt"
        key_path = self.certs_dir / f"{safe_name}.key"

        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(key_path, "wb") as f:
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Restrict key file permissions
        os.chmod(key_path, 0o600)

        logger.info(f"{cert_type.value} certificate generated: {cert_path}")
        return cert_path, key_path

    def get_certificate_info(self, cert_path: Path) -> CertificateInfo:
        """
        Extract information from a certificate.

        Args:
            cert_path: Path to certificate file

        Returns:
            CertificateInfo with certificate details
        """
        if not HAS_CRYPTOGRAPHY:
            raise ImportError("cryptography library required")

        with open(cert_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read(), default_backend())

        def name_to_dict(name: x509.Name) -> Dict[str, str]:
            result = {}
            for attr in name:
                result[attr.oid._name] = attr.value
            return result

        # Check if CA
        is_ca = False
        try:
            bc = cert.extensions.get_extension_for_class(x509.BasicConstraints)
            is_ca = bc.value.ca
        except x509.ExtensionNotFound:
            pass

        # Get key info
        public_key = cert.public_key()
        if isinstance(public_key, rsa.RSAPublicKey):
            key_type = "RSA"
            key_size = public_key.key_size
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            key_type = "EC"
            key_size = public_key.curve.key_size
        else:
            key_type = "Unknown"
            key_size = 0

        return CertificateInfo(
            subject=name_to_dict(cert.subject),
            issuer=name_to_dict(cert.issuer),
            serial_number=cert.serial_number,
            not_valid_before=cert.not_valid_before_utc,
            not_valid_after=cert.not_valid_after_utc,
            is_ca=is_ca,
            key_type=key_type,
            key_size=key_size,
        )

    def check_expiration(
        self, cert_path: Path, warn_days: int = 30
    ) -> tuple[bool, int]:
        """
        Check if certificate is expired or expiring soon.

        Args:
            cert_path: Path to certificate file
            warn_days: Days before expiration to warn

        Returns:
            Tuple of (is_valid, days_until_expiration)
        """
        info = self.get_certificate_info(cert_path)
        now = datetime.utcnow()

        if now > info.not_valid_after:
            return False, 0

        days_remaining = (info.not_valid_after - now).days

        if days_remaining <= warn_days:
            logger.warning(
                f"Certificate {cert_path.name} expires in {days_remaining} days"
            )

        return True, days_remaining
