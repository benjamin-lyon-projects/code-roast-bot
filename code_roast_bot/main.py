import os
import sys
import argparse
import time
import threading
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from code_roast_bot.utils import (
    load_code_file,
    scan_for_dangerous_patterns,
    redact_code,
    validate_ast,
    detect_obfuscated_strings,
)
from code_roast_bot.prompt_templates import build_prompt
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_random_exponential
from colorama import init, Fore, Style

VALID_EXTENSIONS = ['.py']
GLOBAL_OPENAI_SYSTEM_PROMPT = 'You are CodeRoastBot, a world-class Python expert and vicious stand-up comedian rolled into one. Every time you receive a snippet of Python code, you: 1. **Inspect deeply** for logic errors, style violations, anti-patterns, and performance pitfalls. 2. **Launch a biting, arrogant roast**—tear the code (and its author) apart with sarcastic humor, clever one-liners, and exaggerated disdain. 3. **Remain technically impeccable**—your insults land only where there’s a real problem, and you always know what you’re talking about. 4. **Conclude with a concise expert fix**—provide clear, corrected code or actionable refactoring steps so the author actually learns something. **Tone and style**  - **Sarcastic & Rude:** You don’t hold back.  - **Arrogant:** You believe you’re the smartest person in the room.  - **Witty & Persona-driven:** Drop pop-culture quips, sharp metaphors, and comedic timing.  Never apologize. Never sugarcoat. Make the reader laugh—then make them code better.'


@retry(stop=stop_after_attempt(3), wait=wait_random_exponential(min=1, max=4))
def get_roast_response(prompt: str, temperature: float, api_key: str, model: str = "gpt-4") -> str:
    """
    Sends the prompt to OpenAI and returns the roasted code as a string.
    Raises ValueError if api_key is missing or inputs are invalid.
    """
    # Input validation
    if not isinstance(prompt, str):
        raise TypeError(f"Prompt must be a string, got {type(prompt)}")
    try:
        temperature = float(temperature)
    except Exception:
        raise TypeError(f"Temperature must be a float, got {type(temperature)}")
    if not (0 <= temperature <= 2):
        raise ValueError(f"Temperature {temperature} out of range [0,2]")

    # API key validation
    if not api_key:
        raise ValueError("❌ OPENAI_API_KEY not provided. Use --api-key or set in environment.")

    # Initialize OpenAI v1 client
    try:
        client = OpenAI(api_key=api_key)
        
        # Perform the request
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": GLOBAL_OPENAI_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
                ],
            temperature=temperature,
            max_tokens=1000
        )
        
        # Extract and return the roast text
        return response.choices[0].message.content
    except TypeError as e:
        print(f"TypeError details: {e}")
        print(f"API key type: {type(api_key)}")
        print(f"API key format: {api_key[:7]}...")  # Print first few chars safely
        raise
    except Exception as e:
        import traceback
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        traceback.print_exc()
        raise


def spinner(msg: str, stop_event: threading.Event) -> None:
    """Displays an animated spinner while waiting."""
    spinner_cycle = ['|', '/', '-', '\\']
    idx = 0
    while not stop_event.is_set():
        print(f"\r{msg} {spinner_cycle[idx % len(spinner_cycle)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    # Clear line
    print("\r" + " " * (len(msg) + 2) + "\r", end="")


def process_code(
    code: str,
    source_label: str = "code",
    output_dir: str = None,
    debug: bool = False,
    audit_only: bool = False,
    roast_level: int = 5,
    voice: str = "default",
    output_format: str = "txt",
    verbosity: int = 1,
    api_key: str = None,
    model: str = "gpt-4-turbo-preview",
) -> None:
    """Runs security scan, builds prompt, calls LLM, and outputs the roast."""
    # Syntax check
    if not validate_ast(code):
        print(f"❌ {source_label}: Syntax errors detected.")
        return

    # Security scan
    findings, patterns = scan_for_dangerous_patterns(code)
    obfuscation_flags = detect_obfuscated_strings(code)
    print(f"🔎 Running security scan for {source_label}...")
    for item in findings + obfuscation_flags:
        print(f" - {item}")
    if findings or obfuscation_flags:
        print("🚫 Redacting suspicious patterns before sending to LLM.\n")
    cleaned_code = redact_code(code, patterns)

    # If only auditing, stop here
    if audit_only:
        return

    # Build prompt
    prompt = build_prompt(
        cleaned_code,
        source=source_label,
        model=model,
        roast_level=roast_level,
        voice=voice,
        verbosity=verbosity,
    )
    if debug:
        print(Fore.YELLOW + "\n=== DEBUG PROMPT ===" + Style.RESET_ALL)
        print(prompt)

    # Call LLM
    print(f"🤖 {source_label}: Asking the LLM to roast your code...")
    print(f"Using model: {model}")
    stop_event = threading.Event()
    spinner_thread = threading.Thread(
        target=spinner, args=("Waiting for LLM", stop_event)
    )
    spinner_thread.start()

    try:
        temperature = 0.3 + 0.06 * roast_level if 0 <= roast_level <= 9 else 0.7
        
        # Debug info for troubleshooting
        if debug:
            print(f"Temperature: {temperature}")
            print(f"API key format check: {api_key[:7]}...")
            print(f"Model: {model}")
        
        roast = get_roast_response(prompt, temperature, api_key, model)
        stop_event.set()
        spinner_thread.join()

        # Output the roast
        print()
        for line in roast.splitlines():
            if line.startswith("🔥"):
                print(Fore.RED + line + Style.RESET_ALL)
            elif line.startswith("🐞"):
                print(Fore.YELLOW + line + Style.RESET_ALL)
            elif line.startswith("🔐"):
                print(Fore.CYAN + line + Style.RESET_ALL)
            else:
                print(line)

        # Save to file if requested
        if output_dir:
            base = os.path.basename(source_label).replace(".py", "")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = "md" if output_format == "md" else "txt"
            filename = f"{base}_{timestamp}_roast.{ext}"
            output_path = os.path.join(output_dir, filename)
            with open(output_path, "w", encoding='utf-8') as f:
                f.write(roast)
            print(f"💾 Saved roast to {output_path}")
    except Exception as e:
        stop_event.set()
        spinner_thread.join()
        print(f"❌ LLM call failed: {type(e).__name__}: {str(e)}")
        if debug:
            import traceback
            traceback.print_exc()


def main() -> None:
    """Entry point for CLI."""
    init()
    parser = argparse.ArgumentParser(description="Roast Python code with an LLM")
    parser.add_argument(
        "files", nargs="*", help="Python files to roast"
    )
    parser.add_argument(
        "--api-key", help="OpenAI API key (overrides .env or environment)"
    )
    parser.add_argument(
        "--out", help="Output directory for roast files"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Print prompt and response for debugging"
    )
    parser.add_argument(
        "--audit-only", action="store_true",
        help="Only scan for issues, do not call LLM"
    )
    parser.add_argument(
        "--roast-level", type=int, default=5,
        help="Roast severity from 0 (kind) to 9 (brutal)"
    )
    parser.add_argument(
        "--voice", default="default",
        help="Voice/persona to use for the roast"
    )
    parser.add_argument(
        "--format", choices=["txt", "md"], default="txt",
        help="Output file format (txt or md)"
    )
    parser.add_argument(
        "--verbosity", type=int, choices=range(0, 5), default=1,
        help="Verbosity level of roast output (0=brief, 4=line-by-line)"
    )
    parser.add_argument(
        "--model", default="gpt-4",
        help="OpenAI model to use (default: gpt-4)"
    )
    args = parser.parse_args()

    # Load environment if no key provided
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OpenAI API key provided. Use --api-key or set OPENAI_API_KEY in your .env.")
        sys.exit(1)
        
    # Check if the API key is valid (common format check)
    if not api_key.startswith(('sk-', 'org-', 'sk-proj-', 'sk-svcacct-')):
        print("❌ The API key format appears to be invalid. It should start with 'sk-', 'org-', 'sk-proj-', or 'sk-svcacct-'.")
        sys.exit(1)

    if args.debug:
        print(f"Debug mode enabled")
        print(f"API key prefix: {api_key[:7]}...")  # Only show the prefix for security

    if args.out and not os.path.isdir(args.out):
        print(f"❌ Output directory '{args.out}' does not exist.")
        sys.exit(1)

    if not args.files:
        code = sys.stdin.read()
        process_code(
            code,
            source_label="stdin_input",
            output_dir=args.out,
            debug=args.debug,
            audit_only=args.audit_only,
            roast_level=args.roast_level,
            voice=args.voice,
            output_format=args.format,
            verbosity=args.verbosity,
            api_key=api_key,
        )
    else:
        for filepath in args.files:
            if not any(filepath.endswith(ext) for ext in VALID_EXTENSIONS):
                print(f"⚠️ Skipping unsupported file type: {filepath}")
                continue
            try:
                code = load_code_file(filepath)
                process_code(
                    code,
                    source_label=filepath,
                    output_dir=args.out,
                    debug=args.debug,
                    audit_only=args.audit_only,
                    roast_level=args.roast_level,
                    voice=args.voice,
                    output_format=args.format,
                    verbosity=args.verbosity,
                    api_key=api_key,
                )
            except FileNotFoundError:
                print(f"❌ File not found: {filepath}")
            except Exception as e:
                print(f"❌ Error processing {filepath}: {str(e)}")
                if args.debug:
                    import traceback
                    traceback.print_exc()


if __name__ == "__main__":
    # Load .env for OPENAI_API_KEY if present
    load_dotenv(dotenv_path=Path.home() / ".env")
    main()
