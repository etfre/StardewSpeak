using StardewModdingAPI.Utilities;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace StardewSpeak
{
    class ModConfig 
    {
        public KeybindList RestartKey { get; set; } = KeybindList.Parse("LeftControl + LeftShift + R, LeftControl + RightShift + R, RightControl + LeftShift + R, RightControl + RightShift + R");
    }
}
