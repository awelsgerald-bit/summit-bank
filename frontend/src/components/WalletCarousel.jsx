import { useRef, useState } from 'react';
import BankCard from './BankCard';
import BtcCardFace from './BtcCardFace';

export default function WalletCarousel({ usd }) {
  const [index, setIndex] = useState(0); // 0 = USD, 1 = BTC
  const [dragX, setDragX] = useState(0);
  const [dragging, setDragging] = useState(false);
  const drag = useRef({ startX: 0 });

  function onPointerDown(e) {
    drag.current.startX = e.clientX;
    setDragging(true);
    e.currentTarget.setPointerCapture(e.pointerId);
  }
  function onPointerMove(e) {
    if (!dragging) return;
    setDragX(e.clientX - drag.current.startX);
  }
  function onPointerUp() {
    if (!dragging) return;
    const threshold = 60;
    if (dragX < -threshold && index === 0) setIndex(1);
    else if (dragX > threshold && index === 1) setIndex(0);
    setDragging(false);
    setDragX(0);
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