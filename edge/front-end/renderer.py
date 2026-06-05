import pygame

# render a surface to fit within a target rectangle while maintaining aspect ratio
# if the surface is smaller than the target rectangle, it will be centered without scaling
# this renders the camera feed to the left rectangle and the pose images to the right rectangle
def blit_fit(surface, target_surface, target_rect):
    source_rect = surface.get_rect()
    scale = min(target_rect.width / source_rect.width, target_rect.height / source_rect.height)
    scaled_size = (
        max(1, int(source_rect.width * scale)),
        max(1, int(source_rect.height * scale)),
    )
    scaled = pygame.transform.smoothscale(surface, scaled_size)
    scaled_rect = scaled.get_rect(center=target_rect.center)
    target_surface.blit(scaled, scaled_rect)


def draw_centered_status(surface, text, rect, font, color):
    while font.size(text)[0] > rect.width - 20 and len(text) > 3:
        text = text[:-4] + "..."

    rendered = font.render(text, True, color)
    text_rect = rendered.get_rect(center=rect.center)
    surface.blit(rendered, text_rect)


def render(state):
    window = state["window"]
    window.fill(state["BLACK"])

    if state["current_display"] == "start_screen":
        title_rect = state["title_text"].get_rect(center=(state["window_width"] // 2, 120))
        window.blit(state["title_text"], title_rect)

        play_rect = state["play_song_text"].get_rect(center=(state["window_width"] // 2, 300))
        library_rect = state["online_library_text"].get_rect(center=(state["window_width"] // 2, 370))
        leaderboard_rect = state["leaderboard_text"].get_rect(center=(state["window_width"] // 2, 440))

        window.blit(state["play_song_text"], play_rect)
        window.blit(state["online_library_text"], library_rect)
        window.blit(state["leaderboard_text"], leaderboard_rect)

    elif state["current_display"] == "gameplay":
        pygame.draw.rect(window, state["WHITE"], state["left_rect"], state["LINE_WIDTH"])
        pygame.draw.rect(window, state["WHITE"], state["right_rect"], state["LINE_WIDTH"])
        pygame.draw.rect(window, state["WHITE"], state["bottom_rect"], state["LINE_WIDTH"])

        window.blit(state["left_label"], (state["left_rect"].x + state["LABEL_PADDING"], state["left_rect"].y + state["LABEL_PADDING"]))
        window.blit(state["right_label"], (state["right_rect"].x + state["LABEL_PADDING"], state["right_rect"].y + state["LABEL_PADDING"]))
        window.blit(state["bottom_label"], (state["bottom_rect"].x + state["LABEL_PADDING"], state["bottom_rect"].y + state["LABEL_PADDING"]))

        text_surface1 = state["small_font"].render(state["LOADED_SONG"].lyrics[state["current_lyrics_index"] - 1].text, True, state["WHITE"]) 
        text_surface2 = state["big_font"].render(state["LOADED_SONG"].lyrics[state["current_lyrics_index"]].text, True, state["YELLOW"]) 

        text_rect1 = text_surface1.get_rect(center=(state["bottom_rect"].centerx, state["bottom_rect"].top + 80))
        text_rect2 = text_surface2.get_rect(center=state["bottom_rect"].center)

        window.blit(text_surface1, text_rect1)
        window.blit(text_surface2, text_rect2)

        if state["current_lyrics_index"] + 1 < len(state["LOADED_SONG"].lyrics):
            text_surface3 = state["small_font"].render(state["LOADED_SONG"].lyrics[state["current_lyrics_index"] + 1].text, True, state["WHITE"]) 
            text_rect3 = text_surface3.get_rect(center=(state["bottom_rect"].centerx, state["bottom_rect"].bottom - 80))
            window.blit(text_surface3, text_rect3)

        pose_surface = state.get("pose_surface")
        poses = state.get("poses", [])
        if pose_surface is not None:
            blit_fit(pygame.transform.flip(pose_surface, True, False), window, state["left_camera_rect"])
            pose_count = state["status_font"].render(f"poses: {len(poses)}", True, state["WHITE"])
            window.blit(pose_count, (state["left_camera_rect"].x, state["left_camera_rect"].bottom - pose_count.get_height()))
        elif state["pose_camera"].error:
            draw_centered_status(window, state["pose_camera"].error, state["left_camera_rect"], state["status_font"], state["WHITE"])
        else:
            draw_centered_status(window, "Waiting for pose camera...", state["left_camera_rect"], state["status_font"], state["WHITE"])

        pose_img = state["pose_images"][state["current_pose_index"]]
        pose_img_rect = pose_img.get_rect(center=state["right_rect"].center)
        window.blit(pose_img, pose_img_rect)

        # progress bar at bottom of right panel: fills over the duration of the current pose, resets on next pose
        if state.get("game_state") == "playing":
            song_time = pygame.time.get_ticks() - state.get("song_start_time", 0)
            poses = state["LOADED_SONG"].poses
            current_idx = state["current_pose_index"]
            current_start = poses[current_idx].timestamp_ms
            if current_idx + 1 < len(poses):
                duration = poses[current_idx + 1].timestamp_ms - current_start
                progress = max(0.0, min(1.0, (song_time - current_start) / duration)) if duration > 0 else 1.0
            else:
                progress = 1.0
            bar_x = state["right_rect"].x
            bar_y = state["right_rect"].bottom - 14
            bar_w = state["right_rect"].width
            bar_h = 10
            pygame.draw.rect(window, state["WHITE"], (bar_x, bar_y, bar_w, bar_h), 1)
            fill_w = int(bar_w * progress)
            if fill_w > 0:
                pygame.draw.rect(window, state["YELLOW"], (bar_x, bar_y, fill_w, bar_h))

        pygame.draw.rect(window, state["WHITE"], state["button_rect"], state["LINE_WIDTH"])
        window.blit(state["button_text"], (state["button_rect"].x + 15, state["button_rect"].y + 15))

    elif state["current_display"] == "name_entry":
        title = state["name_entry_title_font"].render("ENTER YOUR NAME", True, state["WHITE"])
        window.blit(title, title.get_rect(center=(state["window_width"] // 2, 180)))

        name_text = state["player_name_input"] + "|"
        name_surface = state["name_entry_input_font"].render(name_text, True, state["YELLOW"])
        window.blit(name_surface, name_surface.get_rect(center=(state["window_width"] // 2, state["window_height"] // 2)))

        hint = state["name_entry_hint_font"].render("ENTER to confirm   ESC to go back", True, state["WHITE"])
        window.blit(hint, hint.get_rect(center=(state["window_width"] // 2, state["window_height"] - 60)))

    elif state["current_display"] == "song_library":
        title = state["library_title_font"].render("ONLINE LIBRARY", True, state["WHITE"])
        title_rect = title.get_rect(center=(state["window_width"] // 2, 80))
        window.blit(title, title_rect)

        songs = state["library_songs"]
        selected = state["library_selected_index"]

        if not songs:
            msg = state["library_entry_font"].render("No songs found on server.", True, state["WHITE"])
            window.blit(msg, msg.get_rect(center=(state["window_width"] // 2, state["window_height"] // 2)))
        else:
            entry_start_y = 180
            entry_spacing = 55
            for i, song in enumerate(songs):
                color = state["YELLOW"] if i == selected else state["WHITE"]
                prefix = "> " if i == selected else "  "
                text = f"{prefix}{song['song_title']}  —  {song['artist_name']}"
                surface = state["library_entry_font"].render(text, True, color)
                rect = surface.get_rect(center=(state["window_width"] // 2, entry_start_y + i * entry_spacing))
                window.blit(surface, rect)

        hint = state["library_hint_font"].render("UP/DOWN to navigate   ENTER to select   ESC to go back", True, state["WHITE"])
        window.blit(hint, hint.get_rect(center=(state["window_width"] // 2, state["window_height"] - 50)))

    elif state["current_display"] == "song_confirmed":
        msg = state["library_title_font"].render("Song Selected!", True, state["YELLOW"])
        window.blit(msg, msg.get_rect(center=(state["window_width"] // 2, state["window_height"] // 2 - 50)))
        song_name = state["label_font"].render(state["LOADED_SONG"].song_title, True, state["WHITE"])
        window.blit(song_name, song_name.get_rect(center=(state["window_width"] // 2, state["window_height"] // 2 + 10)))
        hint = state["library_hint_font"].render("Press any key to continue", True, state["WHITE"])
        window.blit(hint, hint.get_rect(center=(state["window_width"] // 2, state["window_height"] - 60)))

    elif state["current_display"] == "leaderboard_song_select":
        # song picker shown before the leaderboard so the user can choose which song to view
        title = state["library_title_font"].render("LEADERBOARD — SELECT SONG", True, state["WHITE"])
        window.blit(title, title.get_rect(center=(state["window_width"] // 2, 80)))

        songs = state.get("leaderboard_songs", [])
        selected = state.get("leaderboard_song_select_index", 0)

        if not songs:
            msg = state["library_entry_font"].render("No songs found on server.", True, state["WHITE"])
            window.blit(msg, msg.get_rect(center=(state["window_width"] // 2, state["window_height"] // 2)))
        else:
            entry_start_y = 180
            entry_spacing = 55
            for i, song in enumerate(songs):
                color = state["YELLOW"] if i == selected else state["WHITE"]
                prefix = "> " if i == selected else "  "
                text = f"{prefix}{song['song_title']}  —  {song['artist_name']}"
                surface = state["library_entry_font"].render(text, True, color)
                rect = surface.get_rect(center=(state["window_width"] // 2, entry_start_y + i * entry_spacing))
                window.blit(surface, rect)

        hint = state["library_hint_font"].render("UP/DOWN to navigate   ENTER to select   ESC to go back", True, state["WHITE"])
        window.blit(hint, hint.get_rect(center=(state["window_width"] // 2, state["window_height"] - 50)))

    elif state["current_display"] == "leaderboard":
        title_rect = state["leaderboard_title_text"].get_rect(center=(state["window_width"] // 2, 100))
        window.blit(state["leaderboard_title_text"], title_rect)

        entry_start_y = 200
        entry_spacing = 60

        if not state["leaderboard_entries"]:
            msg = state["leaderboard_entry_font"].render("No scores yet.", True, state["WHITE"])
            window.blit(msg, msg.get_rect(center=(state["window_width"] // 2, state["window_height"] // 2)))
        else:
            for index, entry in enumerate(state["leaderboard_entries"]):
                entry_string = f"{entry.rank}.  {entry.player_name:<10}  {entry.score}%"
                entry_surface = state["leaderboard_entry_font"].render(entry_string, True, state["WHITE"])
                entry_rect = entry_surface.get_rect(center=(state["window_width"] // 2, entry_start_y + index * entry_spacing))
                window.blit(entry_surface, entry_rect)

        hint_rect = state["leaderboard_hint_text"].get_rect(center=(state["window_width"] // 2, state["window_height"] - 60))
        window.blit(state["leaderboard_hint_text"], hint_rect)

    elif state["current_display"] == "end_screen":
        song_name_rect = state["end_song_name_text"].get_rect(center=(state["window_width"] // 2, 150))
        window.blit(state["end_song_name_text"], song_name_rect)

        score_rect = state["end_score_text"].get_rect(center=(state["window_width"] // 2, state["window_height"] // 2))
        window.blit(state["end_score_text"], score_rect)

        hint_rect = state["end_hint_text"].get_rect(center=(state["window_width"] // 2, state["window_height"] - 80))
        window.blit(state["end_hint_text"], hint_rect)

    pygame.display.flip()
