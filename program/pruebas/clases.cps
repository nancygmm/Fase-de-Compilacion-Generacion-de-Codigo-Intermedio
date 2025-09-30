function toString(x: integer): string { return ""; }

class Vec2 {
  let x: integer;
  let y: integer;

  function constructor(x: integer, y: integer) {
    this.x = x;
    this.y = y;
  }

  function add(dx: integer, dy: integer): void {
    this.x = this.x + dx;
    this.y = this.y + dy;
  }

  function dot(ox: integer, oy: integer): integer {
    return (this.x * ox) + (this.y * oy);
  }
}

let log: string = "";

let a: Vec2 = new Vec2(2, 3);
let b: Vec2 = new Vec2(5, -1);
let cx: integer = a.x + b.x;
let cy: integer = a.y + b.y;
let c: Vec2 = new Vec2(cx, cy);
let d: integer = a.dot(b.x, b.y);

log = log + "c.x=" + toString(c.x) + ", c.y=" + toString(c.y) + "\n";
log = log + "dot=" + toString(d) + "\n";
