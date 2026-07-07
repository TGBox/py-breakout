import pygame
import sys
from game import Game

# DONE TODO: BUG: Sticky paddle needs to allow for angled shots when the ball sticks to it non-centered.
# TODO: FEATURE: Add a screen that tells the player when a level has been completed. Should contain the current level number, (score?), and buttons to get back to the main menu, the editor or play the next level.
# TODO: FEATURE: The main menu should have a link that opens the editor.
# TODO: BUG: Regular bricks shouldn't spawn power ups as often.
# TODO: FEATURE: Add more power ups.
# TODO: FEATURE: Add more block types.
# TODO: BUG: Sticky paddle needs to have a stricter timer.
# TODO: FEATURE: Multiple effects currently already stack together, but multiple power ups of the same type could maybe increase the level of the effect, depending on the type. (e.g. wider paddle gives an even wider paddle when collected twice. but slower ball shouldn't bring the game speed down to unplayable levels.)
# TODO: FEATURE: Background of the game should be something more exciting.
# TODO: FEATURE: Effects for the ball and for breaking blocks.
# TODO: FEATURE: Winning animation; maybe some fireworks or similar.
# TODO: FEATURE: Add inverted control negative power up.
# TODO: FEATURE: Add option to reset all progress in the main menu.
# TODO: FEATURE: Adjust the color scheme for blocks in order for them to be visually different from each other and so that they indicate their health.
# TODO: BUG: Adjust colors for the power ups, so that the text on them is still visible, even if they have a darker background color.

if __name__ == "__main__":
    pygame.init()
    game = Game()
    game.run()
    
    pygame.quit()
    sys.exit()