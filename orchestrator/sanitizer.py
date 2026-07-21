import html
from html.parser import HTMLParser


class SafeHTMLSanitizer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.allowed_tags = {
            'p', 'br', 'strong', 'em', 'u', 'b', 'i', 'span', 'div',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li',
            'blockquote', 'code', 'pre', 'hr', 'a', 'table', 'thead',
            'tbody', 'tr', 'th', 'td'
        }
        self.allowed_attrs = {
            'a': {'href', 'target', 'title', 'rel'},
            'span': {'class', 'style'},
            'div': {'class', 'style'},
            'p': {'class', 'style'}
        }
        self.skip_content_tags = {'script', 'style', 'iframe', 'object', 'embed', 'form'}
        self.skip_level = 0
        self.result = []
        self.tag_stack = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in self.skip_content_tags:
            self.skip_level += 1
            return
        if self.skip_level > 0:
            return
        if tag_lower in self.allowed_tags:
            cleaned_attrs = []
            allowed_attr_names = self.allowed_attrs.get(tag_lower, set())
            for name, value in attrs:
                name_lower = name.lower()
                if name_lower in allowed_attr_names:
                    if name_lower == 'href':
                        val_lower = value.strip().lower()
                        if val_lower.startswith(('javascript:', 'data:', 'vbscript:')):
                            continue
                    cleaned_attrs.append(f'{name}="{html.escape(value)}"')
            attr_str = f" {' '.join(cleaned_attrs)}" if cleaned_attrs else ""
            self.result.append(f"<{tag_lower}{attr_str}>")
            self.tag_stack.append(tag_lower)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.skip_content_tags:
            if self.skip_level > 0:
                self.skip_level -= 1
            return
        if self.skip_level > 0:
            return
        if tag_lower in self.allowed_tags:
            if self.tag_stack and self.tag_stack[-1] == tag_lower:
                self.tag_stack.pop()
                self.result.append(f"</{tag_lower}>")
            elif tag_lower in self.tag_stack:
                while self.tag_stack:
                    closed_tag = self.tag_stack.pop()
                    self.result.append(f"</{closed_tag}>")
                    if closed_tag == tag_lower:
                        break

    def handle_data(self, data):
        if self.skip_level > 0:
            return
        self.result.append(html.escape(data))

    def handle_entityref(self, name):
        if self.skip_level > 0:
            return
        self.result.append(f"&{name};")

    def handle_charref(self, name):
        if self.skip_level > 0:
            return
        self.result.append(f"&#{name};")

    def get_sanitized_html(self) -> str:
        while self.tag_stack:
            self.result.append(f"</{self.tag_stack.pop()}>")
        return "".join(self.result)


def sanitize_html(html_content: str) -> str:
    if not html_content:
        return ""
    parser = SafeHTMLSanitizer()
    try:
        parser.feed(html_content)
        return parser.get_sanitized_html()
    except Exception:
        return html.escape(html_content)
