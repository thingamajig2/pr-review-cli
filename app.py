from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from anthropic import Anthropic

app = Flask(__name__)
CORS(app)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def review_code(code: str) -> str:
    """Send code to Claude for review."""
    # Add line numbers to code for reference
    lines = code.split('\n')
    numbered_code = '\n'.join(f"{i+1:3d} | {line}" for i, line in enumerate(lines))

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are a code reviewer. Review this code and be SPECIFIC - reference line numbers and quote problematic code.

For each issue:
1. State the line number(s)
2. Quote the specific code
3. Explain the problem
4. Suggest a fix

Focus on:
- Bugs or potential issues
- Performance problems
- Code style/readability
- Security concerns
- Better approaches

Code:
```
{numbered_code}
```"""
            }
        ]
    )
    return message.content[0].text


@app.route("/api/review", methods=["POST"])
def review():
    """API endpoint for code review."""
    try:
        data = request.json
        code = data.get("code", "").strip()

        if not code:
            return jsonify({"error": "No code provided"}), 400

        review_text = review_code(code)
        return jsonify({"review": review_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def index():
    """Serve the frontend."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Code Reviewer</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }

            .container {
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 1000px;
                width: 100%;
                padding: 40px;
            }

            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 28px;
            }

            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 14px;
            }

            .content {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }

            @media (max-width: 768px) {
                .content {
                    grid-template-columns: 1fr;
                }
            }

            .section {
                display: flex;
                flex-direction: column;
            }

            label {
                font-weight: 600;
                color: #333;
                margin-bottom: 8px;
                font-size: 14px;
            }

            textarea {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 13px;
                resize: vertical;
                min-height: 300px;
                transition: border-color 0.2s;
            }

            textarea:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }

            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                margin-top: 20px;
                transition: transform 0.2s, box-shadow 0.2s;
                font-size: 14px;
            }

            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }

            button:active {
                transform: translateY(0);
            }

            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }

            .review-output {
                background: #f8f9fa;
                padding: 16px;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                white-space: pre-wrap;
                word-wrap: break-word;
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 13px;
                line-height: 1.6;
                color: #333;
                max-height: 400px;
                overflow-y: auto;
            }

            .review-output ul {
                list-style: none;
                padding-left: 0;
            }

            .review-output li {
                margin: 8px 0 8px 20px;
            }

            .review-output li:before {
                content: "→ ";
                color: #667eea;
                font-weight: bold;
                margin-left: -16px;
                margin-right: 4px;
            }

            .loading {
                color: #667eea;
                font-style: italic;
            }

            .error {
                color: #e74c3c;
                padding: 12px;
                background: #fadbd8;
                border-radius: 8px;
                border: 1px solid #f5b7b1;
            }

            .hidden {
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AI Code Reviewer</h1>
            <p class="subtitle">Paste your code and get instant AI-powered feedback</p>

            <div class="content">
                <div class="section">
                    <label for="codeInput">Paste your code here:</label>
                    <textarea id="codeInput" placeholder="Paste Python, JavaScript, Java, or any code..."></textarea>
                </div>

                <div class="section">
                    <label for="reviewOutput">Review:</label>
                    <div id="reviewOutput" class="review-output"></div>
                </div>
            </div>

            <button id="reviewBtn">Review Code</button>
        </div>

        <script>
            const reviewBtn = document.getElementById('reviewBtn');
            const codeInput = document.getElementById('codeInput');
            const reviewOutput = document.getElementById('reviewOutput');

            reviewBtn.addEventListener('click', async () => {
                const code = codeInput.value.trim();

                if (!code) {
                    reviewOutput.innerHTML = '<div class="error">Please paste some code first.</div>';
                    return;
                }

                reviewBtn.disabled = true;
                reviewBtn.textContent = 'Reviewing...';
                reviewOutput.innerHTML = '<div class="loading">Analyzing your code...</div>';

                try {
                    const response = await fetch('/api/review', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ code })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        reviewOutput.innerHTML = data.review.replace(/\\n/g, '<br>');
                    } else {
                        reviewOutput.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    }
                } catch (error) {
                    reviewOutput.innerHTML = `<div class="error">Network error: ${error.message}</div>`;
                } finally {
                    reviewBtn.disabled = false;
                    reviewBtn.textContent = 'Review Code';
                }
            });

            codeInput.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    reviewBtn.click();
                }
            });
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True, port=5000)
