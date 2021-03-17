using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using Microsoft.Xna.Framework;
using Newtonsoft.Json;
using StardewSpeak.Pathfinder;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewModdingAPI.Utilities;
using StardewValley;
using StardewValley.Buildings;
using StardewValley.Tools;
using StardewValley.Menus;
using System.Reflection;

namespace StardewSpeak
{
	public static class Input
	{
		private static void MouseEvent(SButton button) 
		{
			dynamic inputState = Utils.GetPrivateField(ModEntry.helper.Input, "CurrentInputState")();
			Utils.GetPrivateField(inputState, "CustomPressedKeys").Add(button);
			Utils.SetPrivateField(inputState, "HasNewOverrides", true);
		}
		public static void LeftClick()
		{
			MouseEvent(SButton.MouseLeft);
		}
	}
}
