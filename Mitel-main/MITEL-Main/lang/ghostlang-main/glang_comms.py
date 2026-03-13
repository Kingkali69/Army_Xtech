class GhostLangProtocol:
    """Core protocol definition for GhostLang communication"""
    
    VERSION = "2.0"
    
    class SecurityLevel(Enum):
        LOW = 0     # Basic encryption for non-sensitive data
        MEDIUM = 1  # Standard for normal operation
        HIGH = 2    # Enhanced for suspected threats
        PARANOID = 3 # Maximum security, highest overhead
    
    class EncodingMode(Enum):
        STANDARD = 0    # Full protocol implementation
        COMPRESSED = 1  # For bandwidth-limited channels
        EMERGENCY = 2   # Bare minimum for critical comms
        STEALTH = 3     # Hidden communication mode
    
    class MessageStructure:
        """Core message structure for GhostLang"""
        
        def __init__(self, content, security_level, encoding_mode):
            self.header = {
                "version": GhostLangProtocol.VERSION,
                "timestamp": time.time(),
                "msg_id": str(uuid.uuid4()),
                "security_level": security_level,
                "encoding_mode": encoding_mode,
            }
            
            # Message body with content
            self.body = content
            
            # Integrity section
            self.integrity = {
                "checksum": None,  # Will be computed during serialization
                "hmac": None,      # Will be added during encryption
                "segment_hashes": [] # For multi-part messages
            }
            
        def serialize(self, encryption_key=None):
            """Create the final protocol message"""
            # Create the base structure
            message_data = {
                "header": self.header,
                "body": self.body
            }
            
            # Add integrity checks
            message_data["integrity"] = {
                "checksum": self._compute_checksum(message_data),
            }
            
            # Apply encryption if security level requires it
            if self.header["security_level"] > GhostLangProtocol.SecurityLevel.LOW.value:
                encrypted_data = self._encrypt_payload(
                    data=message_data,
                    key=encryption_key,
                    security_level=self.header["security_level"]
                )
                
                return encrypted_data
            
            return message_data
