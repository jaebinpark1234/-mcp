# saju — 사주 풀이 스킬 (Claude용)

생년월일시를 말하면 Claude가 사주팔자를 계산하고, 폰에서 보기 편한 손그림 스타일 페이지로 풀이를 만들어 주는 스킬입니다.

- 만세력 계산은 스크립트가 합니다(년·월·일·시주, 음력 변환, 절기, 대운, 세운, 십성, 지장간, 12운성, 공망, 신살, 합충).
- 풀이는 항목마다 **전문 용어 풀이**와 **쉬운 말 풀이**가 함께 나옵니다. 버튼으로 쉬운 풀이만 볼 수도 있습니다.
- 원국, 오행, 성격, 구조와 신살, 공부·진로, 재물, 가족, 건강, 대운, 앞으로 몇 해, 개운법까지 한 페이지에 담습니다.

## 설치

### Claude Code

맥 / 리눅스 터미널:

```bash
git clone https://github.com/jaebinpark1234/-mcp ~/.claude/skills/saju
```

윈도우 PowerShell:

```powershell
git clone https://github.com/jaebinpark1234/-mcp "$HOME\.claude\skills\saju"
```

git이 없으면(맥 / 리눅스):

```bash
mkdir -p ~/.claude/skills/saju && curl -L https://github.com/jaebinpark1234/-mcp/archive/refs/heads/main.tar.gz | tar -xz --strip-components=1 -C ~/.claude/skills/saju
```

설치한 뒤 Claude Code를 새로 엽니다. Python 3.8 이상이 있어야 합니다(추가 설치 없음). 새 버전을 받으려면 `git -C ~/.claude/skills/saju pull`.

### claude.ai (웹·앱)

저장소의 **Code → Download ZIP**으로 받은 파일을 **설정 → 기능(Capabilities) → 스킬**에 올립니다. 코드 실행 기능이 켜져 있어야 계산 스크립트가 돌아갑니다.

## 쓰는 법

그냥 말하면 됩니다.

```
2000년 1월 1일 낮 12시 양력 여자 사주 봐줘
음력 1999년 11월 25일 아침 8시 10분 남자, 사주 풀이 페이지 만들어줘
```

Claude가 먼저 빠진 정보를 묻습니다.

- **성별**: 대운 방향이 달라져서 꼭 필요합니다.
- **오전/오후**: "11시"만 쓰면 낮인지 밤인지 묻습니다.
- **양력/음력**: 말이 없으면 양력으로 봅니다.
- **태어난 지역**: 시각이 시(時)의 경계에 걸릴 때만 묻습니다.
- 시간을 모르면 세 기둥(년·월·일)으로 풉니다.

## 알아 둘 점

- 절기 시각은 약 ±15분 오차가 있습니다. 절기 바로 앞뒤에 태어났다면 만세력 앱과 한 번 비교해 보세요.
- 음력 변환은 천문 계산 방식이라 1900~2100년 대부분의 날짜에서 한국 음력과 일치합니다.
- 시(時)의 경계는 "한국 만세력 기준(30분 보정)"이 기본이고, 출생지 경도를 주면 해의 실제 위치(진태양시)로 계산합니다. 두 기준이 갈리면 경고가 나옵니다.
- 사주는 과학이 아니라 오래된 해석의 틀입니다. 재미와 참고로 보세요.

## 구성

```
saju/
├── SKILL.md                     작업 순서와 원칙
├── scripts/saju_calc.py         만세력 계산기
├── scripts/build_page.py        본문에 스타일·마스코트를 붙여 페이지 완성
├── references/interpretation.md 해석 안내와 참고표
├── assets/                      페이지 뼈대, 스타일, 오행별 마스코트 5종
└── tools/                       설치 안내 페이지를 만드는 도구(스킬 동작에는 쓰이지 않음)
```

계산기만 따로 써도 됩니다.

```bash
python3 scripts/saju_calc.py --date 2000-01-01 --time 12:00 --gender f
```
