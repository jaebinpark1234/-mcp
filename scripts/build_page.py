#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""본문 HTML에 스타일·마스코트·전환 스크립트를 붙여 완성된 페이지를 만든다.

  python3 build_page.py --body body.html --mascot wood --title "갑자일주 사주풀이" --out saju.html

mascot: wood fire earth metal water (일간의 오행)
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

TOGGLE = """
<script>
(function(){
  var a=document.getElementById('v-all'),e=document.getElementById('v-easy');
  if(!a||!e)return;
  function set(easy){
    document.body.classList.toggle('easyonly',easy);
    a.classList.toggle('on',!easy);e.classList.toggle('on',easy);
    a.setAttribute('aria-pressed',String(!easy));e.setAttribute('aria-pressed',String(easy));
  }
  a.addEventListener('click',function(){set(false)});
  e.addEventListener('click',function(){set(true)});
})();
</script>
"""


def read(name):
    with open(os.path.join(ASSETS, name), encoding="utf-8") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--mascot", required=True, choices=["wood", "fire", "earth", "metal", "water"])
    ap.add_argument("--title", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--standalone", action="store_true", help="<!doctype html>까지 넣은 단독 파일로 저장(게시 도구 없이 브라우저로 열 때)")
    a = ap.parse_args()

    with open(a.body, encoding="utf-8") as f:
        body = f.read()
    left = sorted(set(re.findall(r"\{\{.*?\}\}", body, flags=re.S)))
    if left:
        sys.exit("채우지 않은 자리가 %d곳 남았습니다: %s" % (len(left), ", ".join(x[:30] for x in left[:5])))
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    for tag in ("div", "section", "li", "ul", "ol", "span", "p"):
        opens = len(re.findall(r"<%s[\s>]" % tag, body))
        closes = body.count("</%s>" % tag)
        if opens != closes:
            print("경고: <%s> 여는 태그 %d개, 닫는 태그 %d개" % (tag, opens, closes), file=sys.stderr)

    head = "<title>%s</title>\n<meta name=\"claude:viewport-fit-sides\" content=\"cover\">\n" % a.title
    page = head + read("style.html") + "\n" + read("mascot_%s.html" % a.mascot) + "\n" + body + TOGGLE
    if a.standalone:
        page = ("<!doctype html>\n<html lang=\"ko\"><head><meta charset=\"utf-8\">"
                "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
                "<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n"
                + page.replace(TOGGLE, "") + TOGGLE + "</body></html>\n")
        page = page.replace(read("mascot_%s.html" % a.mascot), "</head><body>\n" + read("mascot_%s.html" % a.mascot), 1)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(page)
    print("저장: %s (%d bytes)" % (os.path.abspath(a.out), len(page.encode("utf-8"))))


if __name__ == "__main__":
    main()
