import { useRef, useState } from 'react';
import BankCard from './BankCard';
import BtcCardFace from './BtcCardFace';

const DRAG_THRESHOLD = 10; // pixels of movement before we treat this as a swipe, not a tap

export default function WalletCarousel({ usd }) {
  const [index, setIndex] = useState(0);
  const [dragX, setDragX] = useState(0);
  const [dragging, setDragging] = useState(false);
  const drag = useRef({ startX: 0, pointerId: null, captured: false });

  function onPointerDown(e) {
    drag.current.startX = e.clientX;
    drag.current.pointerId = e.pointerId;
    drag.current.captured = false;
    setDragging(true);
  }

  function onPointerMove(e) {
    if (!dragging) return;
    const delta = e.clientX - drag.current.startX;

    // Only claim the pointer (and start visually dragging) once real movement happens.
    // This lets simple taps on buttons/links inside the card pass through untouched.
    if (!drag.current.captured && Math.abs(delta) > DRAG_THRESHOLD) {
      e.currentTarget.setPointerCapture(drag.current.pointerId);
      drag.current.captured = true;
    }

    if (drag.current.captured) {
      setDragX(delta);
    }
  }

  function onPointerUp() {
    if (drag.current.captured) {
      const threshold = 60;
      if (dragX < -threshold && index === 0) setIndex(1);
      else if (dragX > threshold && index === 1) setIndex(0);
    }
    setDragging(false);
    setDragX(0);
    drag.current.captured = false;
  }

  return (
    <div className="space-y-3">
      <div
        className="overflow-hidden select-none touch-pan-y"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
      >
        <div
          className="flex"
          style={{
            width: '200%',
            transform: `translateX(calc(${-index * 50}% + ${dragX}px))`,
            transition: dragging ? 'none' : 'transform 0.4s cubic-bezier(0.22,1,0.36,1)',
          }}
        >
          <div className="w-1/2 pr-1.5 cursor-grab active:cursor-grabbing">
            <BankCard {...usd} />
          </div>
          <div className="w-1/2 pl-1.5 cursor-grab active:cursor-grabbing">
            <BtcCardFace />
          </div>
        </div>
      </div>
      <div className="flex items-center justify-center gap-1.5">
        {[0, 1].map((i) => (
          <button
            key={i}
            onClick={() => setIndex(i)}
            className="h-1.5 rounded-full transition-all"
            style={{
              width: index === i ? '20px' : '6px',
              background: index === i ? 'var(--pink-accent)' : 'rgba(255,255,255,0.2)',
            }}
          />
        ))}
      </div>
    </div>
  );
}