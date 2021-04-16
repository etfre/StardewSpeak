# StardewSpeak

Play Stardew Valley by voice.

## Getting Started

## Commands
### General
<table>
    <tr>
        <th>Command</th>
        <th>Description</th>
        <th>Example(s)</th>
    </tr>
    <tr>
        <td>&lt;direction&gt;</td>
        <td>Begin moving in a specific direction. Options are north (up), east (right), south (down), west (left), main (up and right), floor (down and right), air (down and left), and wash (up and left). Using a mnemonic with USA states: Maine in the northeast, Florida in the southeast, Arizona in the southwest and Washington in the northwest.</td>
        <td>"north"</td>
    </tr>
    <tr>
        <td>&lt;n&gt; &lt;direction&gt;</td>
        <td>Move <i>n</i> tiles in a direction and stop. Will pathfind around obstacles as long as the target tile is clear.</td>
        <td>"one two west" - move left 12 tiles</td>
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
        <td>Walk towards a game location.</td>
        <td>"go to mines"</td>
    </tr>
    <tr>
        <td>(dig | hoe) &lt;x&gt; by &lt;y&gt;</td>
        <td>Use hoe to dig an <i>x</i> by <i>y</i> grid based on the last two directions faced.</td>
        <td>"dig three by four"</td>
    </tr>
    <tr>
        <td>start planting</td>
        <td>Start planting equipped seeds or fertilizer on available hoe dirt.</td>
        <td>"start planting"</td>
    </tr>
    <tr>
        <td>water crops</td>
        <td>Start watering nearby crops.</td>
        <td>"water crops"</td>
    </tr>
    <tr>
        <td>harvest crops</td>
        <td>Start harvesting fully grown crops.</td>
        <td>"start harvesting"</td>
    </tr>
    <tr>
        <td>Pet animals</td>
        <td>Attempt to pet all animals in the current location. Will sometimes fail if the animals are clumped together or are in tight areas that make pathfinding difficult.</td>
        <td>"pet animals"</td>
    </tr>
    <tr>
        <td>Milk animals</td>
        <td>Attempt to milk all cows and goats in the current location. Will sometimes fail if the animals are clumped together or are in tight areas that make pathfinding difficult.</td>
        <td>"milk animals"</td>
    </tr>
    <tr>
        <td>Start fishing</td>
        <td>Cast fishing rod at maximum distance. If the cast is successful, wait for a nibble and begin reeling.</td>
        <td>"start fishing"</td>
    </tr>
    <tr>
        <td>Catch fish</td>
        <td>Automatically complete fish catching minigame. Will also catch any treasure chests that appear.</td>
        <td>"catch fish"</td>
    </tr>
    <tr>
        <td>talk to &lt;npc&gt;</td>
        <td>Move to an NPC and press action button. If the player is holding a giftable item this will gift that item to the NPC. Will fail if the NPC is not in the current location.</td>
        <td>"talk to Leah"</td>
    </tr>
    <tr>
        <td>Start shopping</td>
        <td>If in a store location (Pierre's General Store, Marnie's house, etc.), move to shopkeeper and press action button.</td>
        <td>"start shopping"</td>
    </tr>
    <tr>
        <td>[open | read] (quests | journal | quest log)</td>
        <td>Open journal</td>
        <td>"read journal"</td>
    </tr>
    <tr>
        <td>go inside</td>
        <td>Go inside the nearest building, including farm buildings.</td>
        <td>"go inside"</td>
    </tr>
    <tr>
        <td>Nearest &lt;item&gt;</td>
        <td>Move to nearest <a href="./lib/speech-client/speech-client/items.py">item</a> by name in current location.</td>
        <td>
            <div>"nearest chest"</div>
            <div>"nearest bee house"</div>
        </td>
    </tr>
    <tr>
        <td>(action | check)</td>
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
    <tr>
        <td>item &lt;item&gt;</td>
        <td>Equip the nth item in the toolbar.</td>
        <td>"item seven"</td>
    </tr>
    <tr>
        <td>equip &lt;tool&gt;</td>
        <td>Equip tool if in inventory.</td>
        <td>
            <div>"equip pickaxe"</div>
            <div>"equip shears"</div>
        </td>
    </tr>
    <tr>
        <td>equip [melee] weapon</td>
        <td>Equip melee weapon if in inventory.</td>
        <td>"equip weapon"</td>
    </tr>
    <tr>
        <td>(next | cycle) toolbar</td>
        <td>Cycle the toolbar.</td>
        <td>"next toolbar"</td>
    </tr>
</table>

### Menus
See the [menus file](menus.md) for a list of available menu-specific commands
