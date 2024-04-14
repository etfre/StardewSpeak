using Microsoft.Xna.Framework;
using StardewValley;
using StardewValley.GameData.FarmAnimals;
using StardewValley.Menus;
using StardewValley.Tools;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace StardewSpeak
{
    public static class Serialization
    {
        public static dynamic SerializeAnimal(FarmAnimal animal) 
        {
            if (!animal.modData.ContainsKey(Utils.TrackingIdKey))
            {
                animal.modData[Utils.TrackingIdKey] = System.Guid.NewGuid().ToString();
            }
            string trackingId = animal.modData[Utils.TrackingIdKey];
            var position = new List<float> { animal.Position.X, animal.Position.Y };

            FarmAnimalData animalData = animal.GetAnimalData();
            bool isMature = animal.age.Value < animalData.DaysToMature;
            string currentProduce = animal.currentProduce.Value;
            bool readyForHarvest = isMature && currentProduce  != "";
            var center = new List<int> { (int)animal.getStandingPosition().X, (int)animal.getStandingPosition().Y };
            return new
            {
                trackingId,
                position,
                center,
                tileX = animal.Tile.X,
                tileY = animal.Tile.Y,
                wasPet = animal.wasPet.Value,
                type = animal.type.Value,
                name = animal.Name,
                isAdult = animal.isAdult(),
                isMature,
                currentProduce,
                readyForHarvest,
                toolUsedForHarvest = animal.GetAnimalData().HarvestTool,
                location = SerializeLocation(animal.currentLocation),
            };
        }
        public static dynamic SerializeCharacter(NPC character) 
        {
            if (!character.modData.ContainsKey(Utils.TrackingIdKey)) 
            {
                character.modData[Utils.TrackingIdKey] = System.Guid.NewGuid().ToString();
            }
            string trackingId = character.modData[Utils.TrackingIdKey];
            var position = new List<float> { character.Position.X, character.Position.Y };
            var center = new List<int> { (int)character.getStandingPosition().X, (int)character.getStandingPosition().Y };
            return new
            {
                name = character.Name,
                trackingId,
                location = SerializeLocation(character.currentLocation),
                tileX = character.Tile.X,
                tileY = character.Tile.Y,
                isMonster = character.IsMonster,
                isInvisible = character.IsInvisible,
                facingDirection = character.FacingDirection,
                position,
                center,
            };
        }

        public static dynamic SerializeGameEvent(Event evt) 
        {
            if (evt == null) return null;
            dynamic serializedEvent = new { evt.id, playerCanMove = Game1.player.CanMove, evt.skipped, evt.skippable };
            if (evt.skippable && !evt.skipped)
            {
                Point mousePosition = Game1.getMousePosition();
                dynamic getSkipBounds = Utils.GetPrivateField(evt, "skipBounds");
                Rectangle skipRect = getSkipBounds.Invoke(evt, new object[] { });
                dynamic skipBounds = Utils.RectangleToClickableComponent(skipRect, mousePosition);
                serializedEvent = Utils.Merge(serializedEvent, new { skipBounds });
            }
            return serializedEvent;
        }
        public static dynamic SerializeLocation(GameLocation location)
        {
            if (location == null) return null;
            return new { name = location.NameOrUniqueName, isOutdoors = location.IsOutdoors };
        }
    }


}
