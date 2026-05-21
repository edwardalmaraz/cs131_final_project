from tempdata import The_Feels

def UI():
    
    print("Song Title:", The_Feels.song_title)
    print()
    print("Artist Name:", The_Feels.artist_name)
    print()
    for lyric in The_Feels.lyrics:
        print(" ", lyric.text)
    print()

if __name__ == "__main__":
    UI()