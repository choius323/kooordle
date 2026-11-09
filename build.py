import json, re, sys, os, glob
from collections import defaultdict, Counter

CHO = list('ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ')
JUNG = list('ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ')
JONG = [''] + list('ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ')
SPLIT = {
    'ㄲ': 'ㄱㄱ', 'ㄸ': 'ㄷㄷ', 'ㅃ': 'ㅂㅂ', 'ㅆ': 'ㅅㅅ', 'ㅉ': 'ㅈㅈ',
    'ㅐ': 'ㅏㅣ', 'ㅒ': 'ㅑㅣ', 'ㅔ': 'ㅓㅣ', 'ㅖ': 'ㅕㅣ', 'ㅘ': 'ㅗㅏ', 'ㅙ': 'ㅗㅏㅣ', 'ㅚ': 'ㅗㅣ',
    'ㅝ': 'ㅜㅓ', 'ㅞ': 'ㅜㅓㅣ', 'ㅟ': 'ㅜㅣ', 'ㅢ': 'ㅡㅣ',
    'ㄳ': 'ㄱㅅ', 'ㄵ': 'ㄴㅈ', 'ㄶ': 'ㄴㅎ', 'ㄺ': 'ㄹㄱ', 'ㄻ': 'ㄹㅁ', 'ㄼ': 'ㄹㅂ', 'ㄽ': 'ㄹㅅ',
    'ㄾ': 'ㄹㅌ', 'ㄿ': 'ㄹㅍ', 'ㅀ': 'ㄹㅎ', 'ㅄ': 'ㅂㅅ',
}
sp = lambda j: SPLIT.get(j, j)

# ===== 설정 =====
POS = '명사'                           # 남길 품사
UNIT = '어휘'                          # 구, 관용구, 속담은 제외
EXCLUDE_TYPE = ('방언', '북한어', '옛말')  # 이 말이 들어간 구분은 제외
SYL = (2, 6)                           # 글자 수 범위
JAMO = (4, 15)                         # 자모 수 범위

def to_jamo(w):
    o = ''
    for ch in w:
        c = ord(ch) - 0xAC00
        o += sp(CHO[c // 588]) + sp(JUNG[c % 588 // 28]) + (sp(JONG[c % 28]) if c % 28 else '')
    return o

def as_list(x):
    return x if isinstance(x, list) else ([] if x is None else [x])

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    src = args[0] if args else '.'
    files = sorted(glob.glob(os.path.join(src, '*.json'))) if os.path.isdir(src) else [src]
    if not files:
        print('json 파일을 찾지 못했어요:', src)
        return

    # --peek : 첫 번째 단어의 전체 구조를 보여 줌
    if '--peek' in sys.argv:
        with open(files[0], encoding='utf-8-sig') as f:
            d = json.load(f)
        print(json.dumps(d['channel']['item'][0], ensure_ascii=False, indent=2))
        return

    words = set()
    st_unit, st_pos, st_type = Counter(), Counter(), Counter()
    word_re = re.compile(rf'[가-힣]{{{SYL[0]},{SYL[1]}}}')

    for i, path in enumerate(files, 1):
        with open(path, encoding='utf-8-sig') as f:
            data = json.load(f)
        for it in as_list(data.get('channel', {}).get('item')):
            wi = it.get('wordinfo') or {}
            senses = as_list(it.get('senseinfo'))
            unit = wi.get('word_unit', '')
            st_unit[unit] += 1
            for si in senses:
                st_pos[si.get('pos', '')] += 1
                st_type[si.get('type', '')] += 1
            if unit != UNIT:
                continue
            ok = any(
                si.get('pos') == POS and not any(t in (si.get('type') or '') for t in EXCLUDE_TYPE)
                for si in senses
            )
            if not ok:
                continue
            w = re.sub(r'[-^\s\d"]', '', wi.get('word', ''))
            if word_re.fullmatch(w):
                words.add(w)
        del data
        print(f'[{i}/{len(files)}] {os.path.basename(path)}  누적 {len(words):,}단어')

    print('\n--- 값 확인 ---')
    print('word_unit:', st_unit.most_common(6))
    print('pos      :', st_pos.most_common(6))
    print('type     :', st_type.most_common(6))

    if not words:
        print('\n단어가 0개예요. python build.py 폴더 --peek 로 구조를 확인해 주세요.')
        return

    by = defaultdict(list)
    for w in words:
        by[len(to_jamo(w))].append(w)

    os.makedirs('dict', exist_ok=True)
    print('\n--- 결과 ---')
    for n in sorted(by):
        if JAMO[0] <= n <= JAMO[1]:
            with open(f'dict/{n}.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(sorted(by[n])))
            print(f'자모 {n}개: {len(by[n]):,}단어')

if __name__ == '__main__':
    main()