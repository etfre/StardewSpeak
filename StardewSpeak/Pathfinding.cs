using Microsoft.Xna.Framework;
using StardewValley;
using StardewValley.TerrainFeatures;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using xTile.ObjectModel;
using xTile.Tiles;

namespace StardewSpeak.Pathfinder
{
    public class Location
    {
        public int X;
        public int Y;
        public int F;
        public int G;
        public int H;
        public Location Parent;
        public bool Preferable = false;
    }

    public class Point2
    {
        public int X;
        public int Y;

        public Point2(int x, int y)
        {
            this.X = x;
            this.Y = y;
        }
    }

    public class Pathfinder
    {
        public static dynamic FindPath(GameLocation location, int startX, int startY, int targetX, int targetY, int cutoff = -1)
        {
            var startPoint = new Point(startX, startY);
            var endPoint = new Point(targetX, targetY);
            if (cutoff < 0) cutoff = int.MaxValue;
            var path = PathFindController.findPath(startPoint, endPoint, PathFindController.isAtEndPoint, location, Game1.player, cutoff);
            return path?.Select(p => new { X = p.X, Y = p.Y }).ToList();
        }

        static List<Location> GetWalkableAdjacentSquares(int x, int y, GameLocation map, List<Location> openList, Dictionary<Tuple<int, int>, bool> passableCache)
        {
            List<Location> list = new List<Location>();

            if (IsPassable(map, x, y - 1, passableCache))
            {
                Location node = openList.Find(l => l.X == x && l.Y == y - 1);
                if (node == null) list.Add(new Location() { Preferable = IsPreferableWalkingSurface(map, x, y), X = x, Y = y - 1 });
                else list.Add(node);
            }

            if (IsPassable(map, x, y + 1, passableCache))
            {
                Location node = openList.Find(l => l.X == x && l.Y == y + 1);
                if (node == null) list.Add(new Location() { Preferable = IsPreferableWalkingSurface(map, x, y), X = x, Y = y + 1 });
                else list.Add(node);
            }

            if (IsPassable(map, x - 1, y, passableCache))
            {
                Location node = openList.Find(l => l.X == x - 1 && l.Y == y);
                if (node == null) list.Add(new Location() { Preferable = IsPreferableWalkingSurface(map, x, y), X = x - 1, Y = y });
                else list.Add(node);
            }

            if (IsPassable(map, x + 1, y, passableCache))
            {
                Location node = openList.Find(l => l.X == x + 1 && l.Y == y);
                if (node == null) list.Add(new Location() { Preferable = IsPreferableWalkingSurface(map, x, y), X = x + 1, Y = y });
                else list.Add(node);
            }

            return list;
        }

        static bool IsPreferableWalkingSurface(GameLocation location, int x, int y)
        {
            //todo, make roads more desireable
            return false;
        }

        public static bool IsPassable(GameLocation loc, int x, int y, Dictionary<Tuple<int, int>, bool> passableCache) 
        {
            bool passable;
            var key = new Tuple<int, int>(x, y);
            if (!passableCache.TryGetValue(key, out passable)) {
                passable = IsPassable(loc, x, y);
                passableCache.Add(key, passable);
            }
            return passable;
        }

        public static bool IsPassable(GameLocation loc, int x, int y)
        {
            foreach (var w in loc.warps)
            {
                if (w.X == x && w.Y == y) return true;
            }
            var vec = new Vector2(x, y);
            if (isTileOccupied(loc, vec) || !loc.isTileOnMap(vec))
            {
                return false;
            }
            var tile = loc.Map.GetLayer("Buildings").Tiles[x, y];
            if (tile != null && tile.TileIndex != -1)
            {
                PropertyValue property = null;
                string value2 = null;
                tile.TileIndexProperties.TryGetValue("Action", out property);
                if (property == null)
                {
                    tile.Properties.TryGetValue("Action", out property);
                }
                if (property != null)
                {
                    value2 = property.ToString();
                    if (value2.StartsWith("LockedDoorWarp"))
                    {
                        return false;
                    }
                    if (!value2.Contains("Door") && !value2.Contains("Passable"))
                    {
                        return false;
                    }
                }
                else if (loc.doesTileHaveProperty(x, y, "Passable", "Buildings") == null)
                {
                    return false;
                }
            }
            if (loc.doesTileHaveProperty(x, y, "NoPath", "Back") != null)
            {
                return false;
            }
            if (loc is Farm)
            {
                var fff = loc as Farm;
                if (fff.getBuildingAt(vec) != null)
                {
                    return false;
                }
            }
            foreach (var rc in loc.resourceClumps)
            {
                
                if (rc.occupiesTile(x, y))
                {
                    return false;
                }
            }
            return true;
        }

        static int ComputeHScore(bool preferable, int x, int y, int targetX, int targetY)
        {
            return (Math.Abs(targetX - x) + Math.Abs(targetY - y)) - (preferable ? 1 : 0);
        }

        public static bool isTileOccupied(GameLocation location, Vector2 tileLocation, string characterToIgnore = "")
        {
            location.objects.TryGetValue(tileLocation, out StardewValley.Object o);
            if (o != null) 
            {
                return !o.isPassable();
            }
            Microsoft.Xna.Framework.Rectangle tileLocationRect = new Microsoft.Xna.Framework.Rectangle((int)tileLocation.X * 64 + 1, (int)tileLocation.Y * 64 + 1, 62, 62);
            for (int i = 0; i < location.characters.Count; i++)
            {
                if (location.characters[i] != null && !location.characters[i].name.Equals(characterToIgnore) && location.characters[i].GetBoundingBox().Intersects(tileLocationRect))
                {
                    return true;
                }
            }
            if (location.terrainFeatures.ContainsKey(tileLocation) && tileLocationRect.Intersects(location.terrainFeatures[tileLocation].getBoundingBox(tileLocation)) && !location.terrainFeatures[tileLocation].isPassable())
            {
                return true;
            }
            if (location.largeTerrainFeatures != null)
            {
                foreach (LargeTerrainFeature largeTerrainFeature in location.largeTerrainFeatures)
                {
                    if (largeTerrainFeature.getBoundingBox().Intersects(tileLocationRect))
                    {
                        return true;
                    }
                }
            }
            var f = location.GetFurnitureAt(tileLocation);
            if (f != null && !f.isPassable())
            {
                return true;
            }
            return false;
        }
    }
}