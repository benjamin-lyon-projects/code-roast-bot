import unicodedata
import re
import tiktoken

def normalize_code(code):
    return unicodedata.normalize("NFKC", code)

def strip_dangerous_comments(code):
    return re.sub(r"#.*?(ignore|forget|disregard).*", "", code, flags=re.IGNORECASE)

def escape_backticks(code):
    return code.replace("```", "`\u200b``")

def estimate_token_count(text, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def get_voice_intro(voice):
    voices = {
        "default": "You are a sarcastic but helpful code reviewer.",
        "gordonramsay": "You're Gordon Ramsay reviewing poorly written Python scripts in the style of Hell's Kitchen.",
        "jeremyclarkson": "You're Jeremy Clarkson critiquing code as if it's a ridiculous car.",
        "donaldtrump": "You're Donald Trump roasting Python code. Big code. Very bad.",
        "stevencolbert": "You're Stephen Colbert roasting code with wit and satire.",
        "billburr": "You're Bill Burr giving a no-nonsense verbal beating to bad code."
    }
    return voices.get(voice.lower(), voices["default"])

def get_roast_style(level):
    tones = [
        "Be extremely polite and constructive.",
        "Use gentle humor but keep it respectful.",
        "Be blunt and critical with some sarcasm.",
        "Roast the code aggressively with lots of sarcasm.",
        "Go full comedy roast mode — make it hurt (but accurate).",
        "Add absurd metaphors and creative insults.",
        "Make it dramatic, like a Shakespearean tragedy.",
        "Imply the code might summon demons.",
        "Invoke existential dread. Dark humor welcome.",
        "Burn it down. Nothing is sacred. Brutal honesty."
    ]
    return tones[min(max(level, 0), 9)]

def get_verbosity_directive(level):
    verbosity_map = {
        0: "Keep the roast and analysis brief and high-level. Summarize key issues in a few short paragraphs.",
        1: "Provide a moderately detailed roast. Focus on major issues, common bugs, and clear security concerns.",
        2: "Provide a detailed roast with clear examples and explanations for each issue. Include some commentary on code style and logic.",
        3: "Provide a highly detailed, section-by-section review. Include line-level criticism, specific suggestions, and verbose security analysis.",
        4: "Perform a line-by-line roast. Be relentless, thorough, and brutally honest. Include sarcastic remarks, commentary, and exact citations."
    }
    return verbosity_map.get(level, verbosity_map[1])

def build_prompt(code, source="code", model="gpt-4", max_tokens=3000, roast_level=5, voice="default", verbosity=1):
    code = normalize_code(code)
    code = strip_dangerous_comments(code)
    code = escape_backticks(code)

    current_tokens = estimate_token_count(code, model=model)
    if current_tokens > max_tokens:
        code_lines = code.splitlines()
        code = "\n".join(code_lines[:1000]) + "\n# [TRUNCATED]"

    persona = get_voice_intro(voice)
    tone = get_roast_style(roast_level)
    detail = get_verbosity_directive(verbosity)

    return f"""{persona}

{tone}

{detail}

Your task:
1. Roast the code according to your persona and tone.
2. Point out legitimate bugs, bad practices, and confusing logic.
3. List potential security concerns.
4. Suggest improvements where possible.

Respond in three sections:

🔥 ROAST  
Funny takedown of the code.

🐞 BUGS & STYLE  
Real issues, bugs, and anti-patterns.

🔐 SECURITY  
Security concerns, bad practices, red flags.

### SOURCE: {source}
### START OF CODE ###
{code}
### END OF CODE ###
"""