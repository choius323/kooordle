import json, re, sys, os, glob
from collections import defaultdict, Counter
from build import to_jamo, as_list

# ===== 설정 =====
POS = '명사'                         # 남길 품사
UNIT = '단어'                        # 구, 관용구, 속담, 문법‧표현은 제외
LEVELS = ('초급', '중급', '고급')     # '없음'은 고유명사·비표준 표기가 많아 제외
SYL = (2, 6)                         # 글자 수 범위
JAMO = (4, 15)                       # 자모 수 범위
DICT_DIR = 'dict'                    # 우리말샘 사전 (여기 있는 단어만 정답으로 씀)
OUT_DIR = 'answers'

def feats(node):
    return {f['att']: f.get('val') for f in as_list((node or {}).get('feat')) if isinstance(f, dict)}

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    src = args[0] if args else '.'
    files = sorted(glob.glob(os.path.join(src, '*.json'))) if os.path.isdir(src) else [src]
    if not files:
        print('json 파일을 찾지 못했어요:', src)
        return

    known = set()
    for p in glob.glob(os.path.join(DICT_DIR, '*.txt')):
        with open(p, encoding='utf-8') as f:
            known |= {x.strip() for x in f if x.strip()}
    if not known:
        print(f'{DICT_DIR} 폴더에 사전이 없어요. build.py를 먼저 실행해 주세요.')
        return

    words, skip = set(), Counter()
    word_re = re.compile(rf'[가-힣]{{{SYL[0]},{SYL[1]}}}')

    for i, path in enumerate(files, 1):
        with open(path, encoding='utf-8-sig') as f:
            data = json.load(f)
        for e in as_list(data['LexicalResource']['Lexicon']['LexicalEntry']):
            info = feats(e)
            if info.get('lexicalUnit') != UNIT or info.get('partOfSpeech') != POS:
                continue
            if info.get('vocabularyLevel') not in LEVELS:
                skip['등급 없음'] += 1
                continue
            w = feats(as_list(e.get('Lemma'))[0]).get('writtenForm', '')
            w = re.sub(r'[-^\s\d]', '', w)
            if not word_re.fullmatch(w):
                skip['글자 수·형태'] += 1
                continue
            if not JAMO[0] <= len(to_jamo(w)) <= JAMO[1]:
                skip['자모 수'] += 1
                continue
            if w not in known:
                skip['우리말샘에 없음'] += 1
                continue
            words.add(w)
        del data
        print(f'[{i}/{len(files)}] {os.path.basename(path)}  누적 {len(words):,}단어')

    print('\n제외:', dict(skip))

    by = defaultdict(list)
    for w in words:
        by[len(to_jamo(w))].append(w)

    os.makedirs(OUT_DIR, exist_ok=True)
    print('\n--- 결과 ---')
    for n in sorted(by):
        with open(f'{OUT_DIR}/{n}.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted(by[n])))
        print(f'자모 {n}개: {len(by[n]):,}단어')
    print(f'합계: {len(words):,}단어')

if __name__ == '__main__':
    main()
