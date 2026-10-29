// Soft organic shapes used as decoration on dark surfaces. Purely visual, hidden from screen readers.
const SETS = {
  welcome: {
    box: '0 0 390 844',
    shapes: [
      ['M-30 540 C 40 500, 140 590, 150 700 C 160 810, 60 890, -40 870 Z', '#4a3680'],
      ['M-20 120 C 40 60, 170 70, 210 150 C 250 230, 150 340, 60 340 C -30 340, -70 190, -20 120 Z', '#1c1530'],
      ['M120 390 C 180 340, 300 360, 322 450 C 344 540, 262 565, 252 645 C 242 725, 122 705, 110 605 C 98 525, 70 430, 120 390 Z', '#b3a5e3'],
      ['M250 505 C 320 445, 425 485, 425 585 C 425 685, 335 725, 275 685 C 215 645, 205 555, 250 505 Z', '#e2c8a4'],
      ['M300 -20 C 360 -30, 430 20, 420 80 C 410 140, 330 120, 300 80 C 280 50, 280 0, 300 -20 Z', '#d88aa0'],
      ['M178 470 C 205 450, 238 470, 232 505 C 226 540, 190 548, 178 528 C 170 512, 164 484, 178 470 Z', '#0e0b14', 0.55],
    ],
  },
  card: {
    box: '0 0 346 178',
    shapes: [
      ['M200 -10 C 260 -20 360 20 350 80 C 340 130 270 110 230 90 C 190 70 170 0 200 -10 Z', '#d88aa0'],
      ['M250 120 C 300 90 370 120 360 180 C 350 230 270 220 240 190 C 220 165 220 140 250 120 Z', '#b3a5e3'],
      ['M-20 130 C 20 100 90 130 100 190 C 108 240 20 230 -20 200 Z', '#4a3680'],
      ['M120 150 C 150 130 190 150 190 190 C 190 220 140 220 120 200 Z', '#e2c8a4'],
    ],
  },
  corner: {
    box: '0 0 390 844',
    shapes: [
      ['M300 -20 C 360 -30, 430 20, 420 80 C 410 140, 330 120, 300 80 C 280 50, 280 0, 300 -20 Z', '#d88aa0'],
      ['M-30 760 C 40 720, 140 790, 150 860 C 160 920, 60 940, -40 920 Z', '#4a3680'],
    ],
  },
};

export default function Blobs({ name = 'corner', className = '', opacity = 1 }) {
  const set = SETS[name];
  return (
    <svg
      aria-hidden="true"
      viewBox={set.box}
      preserveAspectRatio="xMidYMid slice"
      className={`absolute inset-0 w-full h-full pointer-events-none ${className}`}
      style={{ opacity }}
    >
      {set.shapes.map(([d, fill, o], i) => (
        <path key={i} d={d} fill={fill} opacity={o ?? 1} />
      ))}
    </svg>
  );
}
