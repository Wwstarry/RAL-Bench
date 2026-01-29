import time
import server
import demo_api
import demo_sessions
import demo_models
import demo_auth
import demo_exceptions

def main():
    # Start the local HTTP server in a background thread
    srv = server.ServerThread()
    srv.start()
    
    # Give the server a moment to start
    time.sleep(1)

    try:
        # Run all demos
        demo_api.run_demo()
        demo_sessions.run_demo()
        demo_models.run_demo()
        demo_auth.run_demo()
        demo_exceptions.run_demo()
        
        print("\nAll demos completed successfully.")
    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")
        raise
    finally:
        # Ensure server is stopped
        print("\nStopping server...")
        srv.stop()

if __name__ == "__main__":
    main()