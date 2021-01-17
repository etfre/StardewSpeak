using Microsoft.Xna.Framework;
using StardewValley;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using xTile.ObjectModel;
using xTile.Tiles;

namespace StardewBot.Pathfinder
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

    public class Point 
    {
        public int X;
        public int Y;

        public Point(int x, int y) {
            this.X = x;
            this.Y = y;
        }
    }

    public class Pathfinder
    {
        public static List<Point> FindPath(GameLocation location, int startX, int startY, int targetX, int targetY, int cutoff = -1)
        {
            Location current = null;
            Location start = new Location { X = startX, Y = startY };
            Location target = new Location { X = targetX, Y = targetY };
            var openList = new List<Location>();
            var closedList = new List<Location>();
            int g = 0;
            var openGates = OpenGates();

            // start by adding the original position to the open list  
            openList.Add(start);

            while (openList.Count > 0)
            {
                // get the square with the lowest F score  
                var lowest = openList.Min(l => l.F);
                current = openList.First(l => l.F == lowest);

                // add to closed, remove from open
                closedList.Add(current);
                openList.Remove(current);

                // if closed contains destination, we're done
                if (closedList.FirstOrDefault(l => l.X == target.X && l.Y == target.Y) != null) break;

                // if closed has exceed cutoff, break out and fail
                if (cutoff > 0 && closedList.Count > cutoff)
                {
                    //Mod.instance.Monitor.Log("Breaking out of pathfinding, cutoff exceeded");
                    return null;
                }

                var adjacentSquares = GetWalkableAdjacentSquares(current.X, current.Y, location, openList, openGates);
                g = current.G + 1;

                foreach (var adjacentSquare in adjacentSquares)
                {
                    // if closed, ignore 
                    if (closedList.FirstOrDefault(l => l.X == adjacentSquare.X
                        && l.Y == adjacentSquare.Y) != null)
                        continue;

                    // if it's not in open
                    if (openList.FirstOrDefault(l => l.X == adjacentSquare.X
                        && l.Y == adjacentSquare.Y) == null)
                    {
                        // compute score, set parent  
                        adjacentSquare.G = g;
                        adjacentSquare.H = ComputeHScore(adjacentSquare.Preferable, adjacentSquare.X, adjacentSquare.Y, target.X, target.Y);
                        adjacentSquare.F = adjacentSquare.G + adjacentSquare.H;
                        adjacentSquare.Parent = current;

                        // and add it to open
                        openList.Insert(0, adjacentSquare);
                    }
                    else
                    {
                        // test if using the current G score makes the adjacent square's F score lower
                        // if yes update the parent because it means it's a better path  
                        if (g + adjacentSquare.H < adjacentSquare.F)
                        {
                            adjacentSquare.G = g;
                            adjacentSquare.F = adjacentSquare.G + adjacentSquare.H;
                            adjacentSquare.Parent = current;
                        }
                    }
                }
            }

            //make sure path is complete
            if (current == null) return null;
            if (current.X != targetX || current.Y != targetY)
            {
                //Mod.instance.Monitor.Log("No path available.", StardewModdingAPI.LogLevel.Warn);
                return null;
            }

            // if path exists, let's pack it up for return
            var returnPath = new List<Point>();
            while (current != null)
            {
                returnPath.Add(new Point(current.X, current.Y));
                current = current.Parent;
            }
            returnPath.Reverse();
            return returnPath;
        }

        public static HashSet<Tuple<int, int>> OpenGates() {
            var gates = new HashSet<Tuple<int, int>>();
            var objects = Game1.player.currentLocation.Objects;
            foreach (StardewValley.Object obj in objects.Values)
            {
                if (obj.Name == "Gate")
                {
                    var gate = obj as Fence;
                    if (gate.gatePosition.Value != 0) // open gate
                    {
                        gates.Add(new Tuple<int, int>((int)gate.TileLocation.X, (int)gate.TileLocation.Y));
                    }
                }
            }
            return gates;
        } 

        static List<Location> GetWalkableAdjacentSquares(int x, int y, GameLocation map, List<Location> openList, HashSet<Tuple<int, int>> openGates)
        {
            List<Location> list = new List<Location>();

            if (IsPassable(map, x, y - 1, openGates))
            {
                Location node = openList.Find(l => l.X == x && l.Y == y - 1);
                if (node == null) list.Add(new Location() { Preferable = IsPreferableWalkingSurface(map, x, y), X = x, Y = y - 1 });
                else list.Add(node);
            }

            if (IsPassable(map, x, y + 1, openGates))
            {
                Location node = openList.Find(l => l.X == x && l.Y == y + 1);
                if (node == null) list.Add(new Location() { Preferable = IsPreferableWalkingSurface(map, x, y), X = x, Y = y + 1 });
                else list.Add(node);
            }

            if (IsPassable(map, x - 1, y, openGates))
            {
                Location node = openList.Find(l => l.X == x - 1 && l.Y == y);
                if (node == null) list.Add(new Location() { Preferable = IsPreferableWalkingSurface(map, x, y), X = x - 1, Y = y });
                else list.Add(node);
            }

            if (IsPassable(map, x + 1, y, openGates))
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

        // This needs work. Feels like there should just be a magical method to call but what?
        public static bool IsPassable(GameLocation loc, int x, int y, HashSet<Tuple<int, int>> openGates)
        {
            foreach (var w in loc.warps)
            {
                if (w.X == x && w.Y == y) return true;
            }
            var tup = new Tuple<int, int>(x, y);
            if (openGates.Contains(tup)) 
            {
                return true;
            }
            var vec = new Vector2(x, y);
            if (loc.isTileOccupiedIgnoreFloors(vec) || !loc.isTileOnMap(vec)) 
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
            if (loc.isTerrainFeatureAt(x, y))
            {
                return false;
            }
            if (loc is Farm)
            {
                var fff = loc as Farm;
                foreach (var brc in fff.largeTerrainFeatures)
                {
                    var r = brc.getBoundingBox();
                    var xx = x;
                    var yy = y;
                    if (xx > r.X && xx < r.X + r.Width && yy > r.Y && yy < r.Y + r.Height) return false;
                }
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
            foreach (var obj in loc.Objects.Values)
            {
                if (obj.TileLocation.X == x && obj.TileLocation.Y == y)
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
    }
}