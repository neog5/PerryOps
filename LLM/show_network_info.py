"""
Display network information for accessing the PerryOps API from other devices.
"""

import socket
import platform


def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Create a socket and connect to an external address
        # This doesn't actually send data, just determines the route
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "Unable to determine"


def get_hostname():
    """Get the hostname of this machine."""
    try:
        return socket.gethostname()
    except Exception:
        return "Unknown"


def main():
    """Display network information."""
    print("=" * 70)
    print("PerryOps API - Network Access Information")
    print("=" * 70)
    print()
    
    hostname = get_hostname()
    local_ip = get_local_ip()
    port = 8000
    
    print("🖥️  Computer Information:")
    print(f"   Hostname: {hostname}")
    print(f"   OS: {platform.system()} {platform.release()}")
    print()
    
    print("🌐 Network Information:")
    print(f"   Local IP Address: {local_ip}")
    print(f"   API Port: {port}")
    print()
    
    print("📱 Access API from Other Devices:")
    print()
    print("   From this computer:")
    print(f"   → http://localhost:{port}")
    print(f"   → http://localhost:{port}/docs")
    print()
    
    if local_ip != "Unable to determine":
        print("   From other devices on the same WiFi/network:")
        print(f"   → http://{local_ip}:{port}")
        print(f"   → http://{local_ip}:{port}/docs")
        print()
        
        print("📝 Example API Calls from Other Devices:")
        print()
        print("   Python:")
        print(f'   BASE_URL = "http://{local_ip}:{port}"')
        print('   response = requests.get(f"{BASE_URL}/health")')
        print()
        
        print("   JavaScript:")
        print(f"   const API_URL = 'http://{local_ip}:{port}';")
        print("   fetch(`${API_URL}/health`);")
        print()
        
        print("   cURL:")
        print(f"   curl http://{local_ip}:{port}/health")
        print()
    
    print("⚠️  Important Notes:")
    print()
    print("   1. Make sure the API is running: python app.py")
    print("   2. Ensure Windows Firewall allows port 8000")
    print("   3. All devices must be on the same network (WiFi/LAN)")
    print()
    
    print("🔥 Windows Firewall Configuration:")
    print()
    print("   Run this in PowerShell as Administrator:")
    print("   New-NetFirewallRule -DisplayName 'PerryOps API' -Direction Inbound \\")
    print("       -LocalPort 8000 -Protocol TCP -Action Allow")
    print()
    
    print("🌍 For Internet Access (External Devices):")
    print()
    print("   Option 1 - Ngrok (Quick Testing):")
    print("   1. Install ngrok: https://ngrok.com/download")
    print("   2. Run: ngrok http 8000")
    print("   3. Use the provided URL (e.g., https://abc123.ngrok.io)")
    print()
    print("   Option 2 - Cloud Deployment (Production):")
    print("   • Deploy to Railway.app, Heroku, or AWS")
    print("   • See NETWORK_ACCESS.md for detailed instructions")
    print()
    
    print("=" * 70)
    print("For more details, see: NETWORK_ACCESS.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
