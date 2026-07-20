import pygame
import sys
from game import Game

# DONE TODO: BUG: Sticky paddle needs to allow for angled shots when the ball sticks to it non-centered.
# DONE TODO: FEATURE: Add option to reset all progress in the main menu.
# DONE TODO: FEATURE: The level number should be clearly visible when playing any given level. This could get handled with the title of the window where the game is running, or it could display a text in the background of the level.
# DONE TODO: FEATURE: The main menu should have a link that opens the editor.
# DONE TODO: BUG: Regular bricks shouldn't spawn power ups as often.
# DONE TODO: BUG: Sticky paddle needs to have a stricter timer.
# DONE TODO: FEATURE: Add a scoring system that calculates a score based on the amount of time that is needed to pass the level. Should also account for the amount and types of extras that you collect. Score should be visible at all times and should get shown again when a level has been completed.
# DONE TODO: FEATURE: Add a highscore system so that players can record their best runs.
# DONE TODO: FEATURE: Add a screen that tells the player when a level has been completed. Should contain the current level number, (score?), and buttons to get back to the main menu, the editor or play the next level.
# TODO: BUG: The highscore view is not working as intended! FIX!
# TODO: BUG: The health calculation for the larger blocks does not change their colors accordingly!
# TODO: BUG: The power up blocks should only spawn power ups. No power downs!
# TODO: FEATURE: Add new block type, that will only spawn power downs! (Needs to get factored in, when calculating the win condition. Every other block must be hit to win; except for them!)
# TODO: BUG: Power ups should not get inverted, when picking up the equivalent power down! This should only revert the state to the regular state.
# TODO: BUG: When picking up a slow motion power up, the score keeps decreasing with the regular rate. Should get adjusted to also only rise with the lower speed while this power up is active!
# TODO: FEATURE: Add new power up that increases points gained or decreases points lost. Add equivalent power down element!
# TODO: FEATURE: Add a difficulty setting that will influence game speed, block health and power up distribution.
# TODO: FEATURE: Add more power ups.
# TODO: FEATURE: Add a secure border power up. This will create a temporary line beneath our paddle and will deflect any ball that we might miss with our paddle back into the game area.
# TODO: FEATURE: Add a magnet power up. Should attract the ball very slightly to move towards our paddle when already in a downwards decent. Should also affect the power ups that have been spawned and attract them to the paddle, as well. The attraction towards the power ups should be greater than the attraction to the ball, to make it harder for the player to avoid a negative effect. Maybe the ball magnet and the power up magnet should be two different power ups? Think about which way of implementing this would be the most beneficial.
# TODO: FEATURE: Add more block types.
# TODO: FEATURE: Multiple effects currently already stack together, but multiple power ups of the same type could maybe increase the level of the effect, depending on the type. (e.g. wider paddle gives an even wider paddle when collected twice. but slower ball shouldn't bring the game speed down to unplayable levels.)
# TODO: FEATURE: Background of the game should be something more exciting.
# TODO: FEATURE: Effects for the ball and for breaking blocks.
# TODO: FEATURE: Winning animation; maybe some fireworks or similar.
# TODO: FEATURE: Add inverted control negative power up.
# TODO: FEATURE: Adjust the color scheme for blocks in order for them to be visually different from each other and so that they indicate their health.
# TODO: BUG: Adjust colors for the power ups, so that the text on them is still visible, even if they have a darker background color.

if __name__ == "__main__":
    pygame.init()
    game = Game()
    game.run()
    
    pygame.quit()
    sys.exit()