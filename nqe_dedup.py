import http.server
import socketserver
import urllib.parse
import re
import html

PORT = 8000

def process_text(text):
    lines = text.strip().split('\n')
    output_lines = []
    
    for line in lines:
        if not line.strip():
            continue
            
        # Match the left side (up to the '=') and the right side (the functions)
        match = re.match(r'^(.*?=\s*)(.*?)(\s*;?\s*)$', line)
        if match:
            prefix = match.group(1)       
            funcs_str = match.group(2)    
            suffix = match.group(3)       
            
            if not suffix.strip():
                suffix = ';'
                
            funcs = [f.strip() for f in funcs_str.split('+')]
            unique_funcs = list(set(funcs))
            
            # Natural sort: splits string by numbers and turns digits into actual integers
            def natural_keys(t):
                return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', t)]
                
            # Sort the deduplicated list 
            unique_funcs.sort(key=natural_keys)
            
            # Reconstruct the string
            processed_line = prefix + ' + '.join(unique_funcs) + suffix.strip()
            output_lines.append(processed_line)
        else:
            output_lines.append(line)
            
    return '\n'.join(output_lines)

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(self.get_html("", "").encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode("utf-8")
        parsed_data = urllib.parse.parse_qs(post_data)
        
        input_text = parsed_data.get('input_data', [''])[0]
        output_text = process_text(input_text)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(self.get_html(input_text, output_text).encode("utf-8"))

    def get_html(self, input_text, output_text):
        safe_input = html.escape(input_text)
        safe_output = html.escape(output_text)
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Function Sorter & Deduplicator</title>
            <style>
                body {{ font-family: sans-serif; margin: 40px; background-color: #f4f4f9; color: #333; }}
                .container {{ max-width: 900px; margin: auto; background: white; padding: 20px 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                textarea {{ width: 100%; box-sizing: border-box; font-family: monospace; font-size: 14px; padding: 12px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px; resize: vertical; }}
                button {{ background-color: #0056b3; color: white; border: none; padding: 10px 24px; cursor: pointer; border-radius: 4px; font-size: 16px; font-weight: bold; }}
                button:hover {{ background-color: #004494; }}
                label {{ font-weight: bold; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Function Sorter & Deduplicator</h2>
                <form method="POST">
                    <label>Paste your input string here:</label><br>
                    <textarea name="input_data" rows="5">{safe_input}</textarea>
                    <button type="submit">Process & Sort</button>
                </form>
                <br>
                <label>Output (Deduplicated and Sorted):</label><br>
                <textarea rows="5" readonly>{safe_output}</textarea>
            </div>
        </body>
        </html>
        """

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        print(f"Server launched successfully! \nGo to: http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.server_close()
