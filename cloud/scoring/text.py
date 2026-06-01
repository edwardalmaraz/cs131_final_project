from difflib import SequenceMatcher

def score_lyrics(text, song):
    matcher = SequenceMatcher(None,text,song)
    print(matcher.ratio())
    return (matcher.ratio() * 100)
