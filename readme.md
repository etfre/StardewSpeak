# StardewSpeak

Play Stardew Valley by voice.

## Getting Started

## Commands
### General
<table>
    <tr>
        <th>Command</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
    <tr>
        <td>&lt;direction&gt;</td>
        <td>Begin moving in a specific direction. Options are north, east, south, west, main, floor, air, wash. Using a mnemonic with USA states: Maine in the northeast, Florida in the southeast, Arizona in the southwest and Washington in the northwest.</td>
        <td>"north"</td>
    </tr>
    <tr>
        <td>&lt;n&gt; &lt;direction&gt;</td>
        <td>Move n tiles and stop.</td>
        <td>"one two west" - move left 12 squares</td>
    </tr>
    <tr>
        <td>Clear debris</td>
        <td>Begin clearing weeds, stone, and wood.</td>
        <td>"clear debris"</td>
    </tr>
    <tr>
        <td>Chop trees</td>
        <td>Begin chopping down nearby trees.</td>
        <td>"chop trees"</td>
    </tr>
    <tr>
        <td>Go to &lt;location&gt;</td>
        <td>Walk towards a fixed location.</td>
        <td>"go to mines"</td>
    </tr>
    <tr>
        <td>Dig &lt;x&gt; by &lt;y&gt;</td>
        <td>Use hoe to dig an <i>x</i> by <i>y</i> grid based on the last two directions faced.</td>
        <td>"dig three by four"</td>
    </tr>
    <tr>
        <td>Water crops</td>
        <td>Start watering nearby crops.</td>
        <td>"water crops"</td>
    </tr>
    <tr>
        <td>Talk to &lt;npc&gt;</td>
        <td>Move to an NPC and press action button. Will fail if the NPC is not in the current location.</td>
        <td>"talk to Leah"</td>
    </tr>
    <tr>
        <td>action</td>
        <td>Press action button (default x)</td>
        <td>"action"</td>
    </tr>
    <tr>
        <td>swing</td>
        <td>Use tool (default c)</td>
        <td>"swing"</td>
    </tr>
    <tr>
        <td>stop</td>
        <td>Stop current actions</td>
        <td>"stop"</td>
    </tr>
</table>

### Menus
See the [menus file](menus.md) for a list of available menu-specific commands
<table>
    <tr>
        <th>Command</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
    <tr>
        <td>Scroll (up  &#124; down)</td>
        <td>Scroll up or down in the list of for sale items.</td>
        <td>"scroll up"</td>
    </tr>
    <tr>
        <td>Page (up  &#124; down)</td>
        <td>Scroll an entire page up or down in the list of for sale items.</td>
        <td>"page down"</td>
    </tr>
</table>