using StardewValley;
using StardewValley.TerrainFeatures;
using StardewValley.Tools;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;

namespace StardewSpeak
{
    public static class GameState
    {
        public static object LastWarp = null;

        public static object PlayerStatus() {
            var player = Game1.player;
            string location = player.currentLocation?.Name;
            var playerPosition = player.Position;
            var position = new List<float>{ playerPosition.X, playerPosition.Y };
            var facingDirection = player.FacingDirection;
            var isMoving = player.isMoving();
            var status = new
            {
                location,
                position,
                tileX = player.getTileX(),
                tileY = player.getTileY(),
                canMove = player.CanMove,
                facingDirection,
                isMoving,
                lastWarp = LastWarp,
            };
            return status;
        }

        public static object PlayerItems() 
        {
            var player = Game1.player;
            var items = player.Items.Select(i => {
                return Utils.SerializeItem(i);
             });
            var cursorSlotItem = Utils.SerializeItem(player.CursorSlotItem);
            var equippedItems = new 
            {
                boots = Utils.SerializeItem(player.boots.Value),
                hat = Utils.SerializeItem(player.hat.Value),
                leftRing = Utils.SerializeItem(player.leftRing.Value),
                pants = Utils.SerializeItem(player.pantsItem.Value),
                rightRing = Utils.SerializeItem(player.rightRing.Value),
                shirt = Utils.SerializeItem(player.shirtItem.Value),
            };
            return new { currentToolIndex = Game1.player.CurrentToolIndex, items, cursorSlotItem, equippedItems };
        }

        public static object CharactersAtLocation(GameLocation location)
        {
            var chars = new List<dynamic>();
            foreach (var character in location.characters) 
            {
                var position = new List<float> { character.Position.X, character.Position.Y };
                var charObj = new
                {
                    name = character.Name,
                    tileX = character.getTileX(),
                    tileY = character.getTileY(),
                    isMonster = character.IsMonster,
                    isInvisible = character.IsInvisible,
                    facingDirection = character.FacingDirection,
                    position,
                };
                chars.Add(charObj);
            }
            return chars;
        }

        public static object ToolStatus()
        {
            var player = Game1.player;
            var tool = player.CurrentTool;
            return Utils.SerializeItem(tool);
        }

        public static object Trees() 
        {
            var features = new List<dynamic>();
            foreach (var tf in Game1.currentLocation.terrainFeatures.Values) 
            {
                if (tf is Tree)
                {
                    var tree = tf as Tree;
                    var tileLocation = tree.currentTileLocation;
                    features.Add(new { 
                        type = "tree",
                        treeType = tree.treeType.Value, 
                        tileX = (int)tileLocation.X, 
                        tileY = (int)tileLocation.Y, 
                        tapped = tree.tapped.Value, 
                        stump = tree.stump.Value,
                        growthStage = tree.growthStage.Value,
                    });
                }
                else 
                {
                
                }
            }
            return features;
        }

        public static object HoeDirtTiles()
        {
            var features = new List<dynamic>();
            foreach (var tf in Game1.currentLocation.terrainFeatures.Values)
            {
                if (tf is HoeDirt)
                {
                    var dirtTile = tf as HoeDirt;
                    var crop = dirtTile.crop == null ? null : new { dirtTile.crop.currentPhase, dead = dirtTile.crop.dead.Value, fullyGrown = dirtTile.crop.fullyGrown.Value };
                    int fertilizer = dirtTile.fertilizer.Value;
                    var tileLocation = dirtTile.currentTileLocation;
                    var tileX = (int)tileLocation.X;
                    var tileY = (int)tileLocation.Y;
                    bool canPlantThisSeedHere = Utils.CanPlantOnHoeDirt(dirtTile);
                    var readyForHarvest = dirtTile.readyForHarvest();
                    var isWatered = dirtTile.state.Value == 1;
                    var needsWatering = dirtTile.needsWatering();
                    features.Add(new { type = "hoeDirt", readyForHarvest, fertilizer, isWatered, needsWatering, tileX, tileY, crop, canPlantThisSeedHere });
                }
                else
                {

                }
            }
            return features;
        }

        public static object ResourceClumps() 
        {
            var clumps = new List<dynamic>();
            foreach (var clump in Game1.currentLocation.resourceClumps) 
            {
                string name = "";
                switch (clump.parentSheetIndex.Value) 
                {
                    case ResourceClump.boulderIndex: 
                        name = "boulder";
                        break;
                    case ResourceClump.hollowLogIndex:
                        name = "hollowLog";
                        break;
                    case ResourceClump.stumpIndex:
                        name = "stump";
                        break;
                    case ResourceClump.meteoriteIndex:
                        name = "meteorite";
                        break;
                    case ResourceClump.mineRock1Index:
                    case ResourceClump.mineRock2Index:
                    case ResourceClump.mineRock3Index:
                    case ResourceClump.mineRock4Index:
                        name = "mineRock";
                        break;
                }
                var serializedClump = new
                {
                    tileX = (int)clump.tile.X,
                    tileY = (int)clump.tile.Y,
                    height = clump.height.Value,
                    width = clump.width.Value,
                    objectIndex = clump.parentSheetIndex.Value,
                    health = clump.health.Value,
                    name
                };
                clumps.Add(serializedClump);
            }
            return clumps;
        }

        public static object Debris()
        {
            var debris = new List<dynamic>();
            foreach (var d in Game1.currentLocation.debris)
            {
                var chunkType = d.chunkType.Value;
                var debrisType = d.debrisType.Value;
                var movingTowardsPlayer = d.chunksMoveTowardPlayer;
                foreach(var chunk in d.Chunks) 
                {
                    var tileX = (int)(chunk.position.X / Game1.tileSize);
                    var tileY = (int)(chunk.position.Y / Game1.tileSize);
                    var isMoving = chunk.xVelocity > 0 || chunk.yVelocity > 0;
                    var debrisObj = new { chunkType, debrisType, tileX, tileY, movingTowardsPlayer, isMoving };
                    debris.Add(debrisObj);
                }
            }
            return debris;
        }

        public static dynamic LocationObjects() 
        {
            var objs = new List<dynamic>();
            foreach (var kvp in Game1.currentLocation.Objects.Pairs) 
            {
                var tileLocation = kvp.Key;
                var tileX = (int)tileLocation.X;
                var tileY = (int)tileLocation.Y;
                var isOnScreen = Utils.isOnScreen(tileLocation, 0, Game1.player.currentLocation);
                var o = kvp.Value;
                bool readyForHarvest = o.readyForHarvest.Value;
                bool canBeGrabbed = o.canBeGrabbed.Value;
                var formattedObj = new {name = o.Name, tileX, tileY, type = o.Type, readyForHarvest, canBeGrabbed, isOnScreen };
                objs.Add(formattedObj);
            }
            return objs;
        }

            
        public static Position PlayerPosition { get; set; }
    }
    public class Position {
        public string location { get; set; }
        public int x { get; set; }
        public int y { get; set; }
        
        public Position(string location, int x, int y) {
            this.location = location;
            this.x = x;
            this.y = y;
        }
    }
}
