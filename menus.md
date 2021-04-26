Generally, menu commands should map to what is visible on screen. For example, if a menu contains an ok button, saying `ok` will click that button. Similarly, saying `trash can` will click on any visible trash can. Adding these commands is a manual process that varies from menu to menu, so if a command is missing or not working correctly feel free to create an issue.

All menus with commands can also be navigated with the `north`, `south`, `east`, and `west` commands to move the mouse to an adjacent clickable section of the active menu. An optional number afterwards will fire the command that many times. For example, if the backpack is open with the mouse over the second item on the first row, saying `south two` will move the cursor to the second item on the third row. `Click` and `right click` will click any button underneath the mouse.

Some menus, like the new game menu, contain text boxes for <a href="./StardewSpeak/lib/speech-client/speech-client/letters.py">free form text entry</a>. Dictation is also available - saying `title hello world` will enter "Hello World", and saying `dictate hello world` will enter "hello world".

## Available Menu Commands (WIP)
* [Title Menu](#title-menu)
* [New Game Menu](#new-game-menu)
* [Load Game Menu](#load-game-menu)
<br></br>
* [Shipping Bin](#shipping-bin)
* [Shop Menu](#shop-menu)
<br/><br/>

### Title Menu
<table>
    <tr>
        <th>Command</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
    <tr>
        <td>new [game]</td>
        <td>Click the new game button.</td>
        <td>"new game"</td>
    </tr>
    <tr>
        <td>load [game]</td>
        <td>Click the load game button.</td>
        <td>"load game"</td>
    </tr>
    <tr>
        <td>co-op [game]</td>
        <td>Click the co-op game button.</td>
        <td>"co-op game"</td>
    </tr>
    <tr>
        <td>exit [game]</td>
        <td>Click the exit game button.</td>
        <td>"exit game"</td>
    </tr>
    <tr>
        <td>[change | select] (language | languages)</td>
        <td>Open the select language menu.</td>
        <td>"change language"</td>
    </tr>
</table>
<br/><br/>

### New Game Menu
<table>
    <tr>
        <th>Command</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
    <tr>
        <td>name</td>
        <td>Click the farmer name box.</td>
        <td>"name"</td>
    </tr>
    <tr>
        <td>farm name</td>
        <td>Click the farm name box.</td>
        <td>"farm name"</td>
    </tr>
    <tr>
        <td>favorite thing</td>
        <td>Click the favorite thing box.</td>
        <td>"favorite thing"</td>
    </tr>
    <tr>
        <td>ok</td>
        <td>Close the co-op help menu if active. Otherwise, starts a new game.</td>
        <td>"ok"</td>
    </tr>
    <tr>
        <td>&lt;farm_name&gt; farm</td>
        <td>Select farm. Options for <i>farm_name</i> are standard, riverland, forest, hilltop, wilderness, four corners, and beach.</td>
        <td>"forest farm"</td>
    </tr>
    <tr>
        <td>(previous | next) &lt;option&gt;</td>
        <td>Select previous or next option. Options for <i>option</i> are accessory, direction, hair, pants, pet, shirt, skin, money style (co-op), profit margin (co-op), and starting cabins (co-op).</td>
        <td>"previous pet"</td>
    </tr>
    <tr>
        <td>(random | [roll] dice)</td>
        <td>Click the dice button to randomize farmer options.</td>
        <td>"random"</td>
    </tr>
    <tr>
        <td>skip (intro | introduction)</td>
        <td>Toggle the Skip Intro checkbox.</td>
        <td>"skip introduction"</td>
    </tr>
    <tr>
        <td>help</td>
        <td>Launch co-op help screen.</td>
        <td>"help"</td>
    </tr>
    <tr>
        <td>(previous | next)</td>
        <td>When the co-op help screen is active, flip to the previous or next page.</td>
        <td>"next"</td>
    </tr>
    <tr>
        <td>[go] back</td>
        <td>Exit to title menu.</td>
        <td>"back"</td>
    </tr>
</table>
<br/><br/>

### Load Game Menu
<table>
    <tr>
        <th>Command</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
    <tr>
        <td>(load [game] | [load] game) &lt;n&gt;</td>
        <td>Load the <i>n</i>th game from the top of the screen </td>
        <td>"load game three"</td>
    </tr>
    <tr>
        <td>scroll (up | down)</td>
        <td>Scroll up or down</td>
        <td>"scroll down"</td>
    </tr>
    <tr>
        <td>page (up | down)</td>
        <td>Scroll up or down four times</td>
        <td>"page up"</td>
    </tr>
    <tr>
        <td>(delete [game] | [delete] game) &lt;n&gt;</td>
        <td>Delete the <i>n</i>th game from the top of the screen </td>
        <td>"delete game three"</td>
    </tr>
    <tr>
        <td>(yes | ok)</td>
        <td>Confirm game deletion</td>
        <td>"ok"</td>
    </tr>
        <tr>
        <td>(no | cancel)</td>
        <td>Cancel game deletion</td>
        <td>"no"</td>
    </tr>
    <tr>
        <td>[go] back</td>
        <td>Exit to title menu.</td>
        <td>"back"</td>
    </tr>
</table>
<br/><br/>

### Containers
Any menu that involves transfers between player items and another container, such as chests.
<table>
    <tr>
        <th>Command</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
    <tr>
        <td>item &lt;n&gt;</td>
        <td>Move the cursor to the nth item in the current row (first by default)</td>
        <td>"item seven"</td>
    </tr>
    <tr>
        <td>row &lt;n&gt;</td>
        <td>Move the cursor to the nth row</td>
        <td>"row three"</td>
    </tr>
    <tr>
        <td>ok</td>
        <td>Click the ok button</td>
        <td>"ok"</td>
    </tr>
    <tr>
        <td>trash can</td>
        <td>Click the trash can. Will discard any selected item.</td>
        <td>"trash can"</td>
    </tr>
</table>
<br/><br/>

### Shipping Bin
<table>
    <tr>
        <th>Command</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
    <tr>
        <td>item &lt;n&gt;</td>
        <td>Move the cursor to the nth item in the current row (first by default)</td>
        <td>"item seven"</td>
    </tr>
    <tr>
        <td>row &lt;n&gt;</td>
        <td>Move the cursor to the nth row</td>
        <td>"row three"</td>
    </tr>
    <tr>
        <td>ok</td>
        <td>Click the ok button</td>
        <td>"ok"</td>
    </tr>
    <tr>
        <td>undo</td>
        <td>Move the most recently shipped item back into the player's backpack</td>
        <td>"undo"</td>
    </tr>
</table>
<br/><br/>

### Shop Menu
<table>
    <tr>
        <th>Command</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
    <tr>
        <td>scroll (up  &#124; down)</td>
        <td>Scroll up or down in the list of for sale items.</td>
        <td>"scroll up"</td>
    </tr>
    <tr>
        <td>page (up  &#124; down)</td>
        <td>Scroll an entire page up or down in the list of for sale items.</td>
        <td>"page down"</td>
    </tr>
</table>