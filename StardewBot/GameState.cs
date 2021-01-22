using StardewValley;
using StardewValley.TerrainFeatures;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;

namespace StardewBot
{
    public static class GameState
    {
        public static object LastWarp = null;

        public static object PlayerStatus() {
            var player = Game1.player;
            string location = player.currentLocation?.Name;
            var playerPosition = player.Position;
            var position = new { x = playerPosition.X, y = playerPosition.Y };
            var facingDirection = player.FacingDirection;
            var isMoving = player.isMoving();
            var status = new
            {
                location,
                position,
                tileX = player.getTileX(),
                tileY = player.getTileY(),
                facingDirection,
                isMoving,
                lastWarp = LastWarp
            };
            return status;
        }

        public static object ToolStatus()
        {
            var player = Game1.player;
            var tool = player.CurrentTool;
            var status = new
            {
                upgradeLevel = tool.UpgradeLevel,
                power = player.toolPower,
                baseName = tool.BaseName,
                inUse = player.UsingTool,
            };
            return status;
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
                    features.Add(new { type = "tree", treeType = tree.treeType.Value, tileX = (int)tileLocation.X, tileY = (int)tileLocation.Y, tapped = tree.tapped.Value, stump = tree.stump.Value });
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
                    var crop = dirtTile.crop == null ? null : new { dead = dirtTile.crop.dead.Value, fullyGrown = dirtTile.crop.fullyGrown.Value };
                    var tileLocation = dirtTile.currentTileLocation;
                    var readyForHarvest = dirtTile.readyForHarvest();
                    var isWatered = dirtTile.state.Value == 1;
                    var needsWatering = dirtTile.needsWatering();
                    features.Add(new { type = "hoeDirt", readyForHarvest, isWatered, needsWatering, tileX = (int)tileLocation.X, tileY = (int)tileLocation.Y, crop });
                }
                else
                {

                }
            }
            return features;
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
            foreach (var o in Game1.currentLocation.Objects.Values) 
            {
                var tileX = (int)o.TileLocation.X;
                var tileY = (int)o.TileLocation.Y;
                var formattedObj = new {name = o.Name, tileX, tileY};
                objs.Add(formattedObj);
            }
            return objs;
        }

        public static object GameValues() 
        {
            var values = new
            {
                tilesize = Game1.tileSize
                //x = Game1.
            };
            return values;
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
