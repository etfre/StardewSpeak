using StardewModdingAPI.Utilities;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace StardewSpeak
{
    public class ModConfig 
    {
        public KeybindList RestartKey { get; set; } = KeybindList.Parse("LeftControl + LeftShift + R, LeftControl + RightShift + R, RightControl + LeftShift + R, RightControl + RightShift + R");
        public KeybindList StopKey { get; set; } = KeybindList.Parse("LeftControl + LeftShift + S, LeftControl + RightShift + S, RightControl + LeftShift + S, RightControl + RightShift + S");
        public bool Debug { get; set; } = false;
    }
}
