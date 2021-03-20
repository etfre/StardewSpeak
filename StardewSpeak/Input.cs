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
		public static Dictionary<string, SButton> Held = new Dictionary<string, SButton>();

		private static void InputEvent(SButton button, bool setDown) 
		{
			MethodInfo overrideButton = Game1.input.GetType().GetMethod("OverrideButton");
			if (overrideButton == null) throw new InvalidOperationException("Can't find 'OverrideButton' method on SMAPI's input class.");
			overrideButton.Invoke(Game1.input, new object[] { button, setDown });
		}
		public static void SetDown(SButton button)
		{
			InputEvent(button, true);
		}
		public static void SetUp(SButton button)
		{
			InputEvent(button, false);
		}

		public static void SetDown(string option)
		{
			var button = OptionToSButton(option);
			SetDown(button);
		}
		public static void SetUp(string option)
		{
			var button = OptionToSButton(option);
			SetUp(button);
		}

		public static SButton OptionToSButton(string name) 
		{
			//InputButton optionBtn = (dynamic)Game1.options.GetType().GetProperty(name).GetValue(Game1.options, null);
			InputButton optionBtn = Utils.GetPrivateField(Game1.options, name)[0];
			return SButtonExtensions.ToSButton(optionBtn);
		}

		public static void Hold(string optionName) 
		{
			if (!Held.ContainsKey(optionName))
			{
				var btn = OptionToSButton(optionName);
				var newHeld = new Dictionary<string, SButton>(Held);
				newHeld.Add(optionName, btn);
				Held = newHeld;
			}
			
		}


		public static void Release(string optionName)
		{
			var newHeld = new Dictionary<string, SButton>(Held);
			newHeld.Remove(optionName);
			Held = newHeld;
		}
		public static void LeftClick()
		{
			SButtonExtensions.ToSButton(Game1.options.inventorySlot8[0]);
			var x = Game1.options.inventorySlot12[0];
			InputEvent(SButton.MouseLeft, true);
		}
	}
}
