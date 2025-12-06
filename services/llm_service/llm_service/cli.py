import sys

def run():
    from llm_service.app.main import serve

    try:
        serve()
    except KeyboardInterrupt:
        print("LLM Service stopped manually.")
        sys.exit(0)
    except Exception as e:
        print(f"LLM Service crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
