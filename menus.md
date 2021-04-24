Generally, menu commands should map to what is visible on screen. For example, if a menu contains an ok button, saying `ok` will click that button. Similarly, saying `trash can` will click on any visible trash can. Adding these commands is a manual process that varies from menu to menu, so if a command is missing or not working correctly feel free to create an issue.

All menus with commands can also be navigated with the `north`, `south`, `east`, and `west` commands to move the mouse to an adjacent clickable section of the active menu. An optional number afterwards will fire the command that many times. For example, if the backpack is open with the mouse over the second item on the first row, saying `south two` will move the cursor to the second item on the third row. `Click` and `right click` will click any button underneath the mouse.

## Available Menu Commands (WIP)

* [Shipping Bin](#shipping-bin)
* [Shop Menu](#shop-menu)

### Title Menu
<table>
    <tr>
        <th>Command</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
    <tr>
        <td>new [game]</td>
        <td>Click the new game button</td>
        <td>"new game"</td>
    </tr>
    <tr>
        <td>load [game]</td>
        <td>Click the load game button</td>
        <td>"load game"</td>
    </tr>
    <tr>
        <td>co-op [game]</td>
        <td>Click the co-op game button</td>
        <td>"co-op game"</td>
    </tr>
    <tr>
        <td>exit [game]</td>
        <td>Click the exit game button</td>
        <td>"exit game"</td>
    </tr>
    <tr>
        <td>[change | select] (language | languages)</td>
        <td>Open the select language menu</td>
        <td>"change language"</td>
    </tr>
</table>

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

### Shop Menu
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