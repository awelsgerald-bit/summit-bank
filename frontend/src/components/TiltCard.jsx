import { useEffect, useRef, useState } from 'react';
import { Anchor, Gift, QrCode, Snowflake, CalendarClock, PiggyBank, Zap, FileText } from 'lucide-react';
import Blobs from './Blobs';

const KEYS = [Zap, PiggyBank, CalendarClock, Snowflake, QrCode, FileText, Gift, Anchor];

// The hero art: a Summit card over a lilac and sand panel. It tilts toward the cursor or a
// finger moving over the art, glints where the light would hit, and flips when tapped.
export default function TiltCard() {
  const stage = useRef(null);
  const frame = useRef(0);
  const [flipped, setFlipped] = useState(false);

  function aim(e) {
    const el = stage.current;
    if (!el) return;
    const box = el.getBoundingClientRect();
    const px = Math.min(1, Math.max(0, (e.clientX - box.left) / box.width));
    const py = Math.min(1, Math.max(0, (e.clientY - box.top) / box.height));
    cancelAnimationFrame(frame.current);
    frame.current = requestAnimationFrame(() => {
      el.style.setProperty('--rx', `${((0.5 - py) * 24).toFixed(2)}deg`);
      el.style.setProperty('--ry', `${((px - 0.5) * 30).toFixed(2)}deg`);
      el.style.setProperty('--gx', `${(px * 100).toFixed(1)}%`);
      el.style.setProperty('--gy', `${(py * 100).toFixed(1)}%`);
      el.dataset.active = '1';
    });
  }

  function rest() {
    const el = stage.current;
    if (!el) return;
    cancelAnimationFrame(frame.current);
    el.style.setProperty('--rx', '0deg');
    el.style.setProperty('--ry', '0deg');
    delete el.dataset.active;
  }

  useEffect(() => () => cancelAnimationFrame(frame.current), []);

  return (
    <div className="relative w-full max-w-[560px] mx-auto">
      <div
        ref={stage}
        className="tilt-stage relative aspect-[1.3] select-none"
        onPointerMove={aim}
        onPointerDown={aim}
        onPointerLeave={rest}
        onPointerCancel={rest}
        onPointerUp={(e) => e.pointerType !== 'mouse' && setTimeout(rest, 450)}
      >
        <div className="absolute left-0 right-0 top-[20%] bottom-[2%] rounded-[28px] overflow-hidden flex" aria-hidden="true">
          <div className="flex-[72] bg-[#b3a5e3]" />
          <div className="flex-[28] bg-[#e2c8a4] grid grid-cols-2 content-center gap-[8%] p-[7%]">
            {KEYS.map((Icon, i) => (
              <span key={i} className={`aspect-square rounded-xl flex items-center justify-center ${i === 3 || i === 5 ? 'bg-[#1a1426] text-white' : 'bg-white/90 text-[#3b2a66]'}`}>
                <Icon size={16} strokeWidth={1.8} />
              </span>
            ))}
          </div>
        </div>

        <div className="tilt-pose absolute left-[7%] top-0 w-[62%]">
          <div className="tilt-float">
            <div className="tilt-body">
              <button
                type="button"
                onClick={() => setFlipped((f) => !f)}
                aria-pressed={flipped}
                aria-label="Summit Bank card. Press to flip it over."
                className="tilt-flip block w-full aspect-[1.586] relative text-left"
                data-flipped={flipped}
              >
                <span className="tilt-face rounded-[6%] overflow-hidden bg-[#14101f] text-white shadow-[0_30px_60px_-20px_rgba(26,20,38,0.55)]">
                  <Blobs name="card" />
                  <span className="glint" />
                  <span className="absolute left-[7%] top-[9%] right-[7%] flex items-center justify-between">
                    <span className="font-display font-semibold text-[clamp(11px,3.6cqw,18px)] flex items-center gap-[6px]"><Anchor size={14} /> Summit Bank</span>
                    <span className="w-[11%] aspect-[1.3] rounded-[4px] bg-[#e2c8a4]/90" />
                  </span>
                  <span className="absolute left-[7%] bottom-[28%] text-[clamp(9px,2.4cqw,12px)] text-white/70">Available balance</span>
                  <span className="absolute left-[7%] bottom-[14%] font-display font-bold text-[clamp(14px,5.2cqw,26px)]">₦75,850.00</span>
                  <span className="absolute left-[7%] bottom-[5%] tracking-[0.2em] text-[clamp(8px,2.3cqw,12px)] text-white/80">5566 3993 7942</span>
                </span>
                <span className="tilt-face tilt-back rounded-[6%] overflow-hidden bg-[#1c1530] text-white shadow-[0_30px_60px_-20px_rgba(26,20,38,0.55)]">
                  <span className="absolute inset-x-0 top-[12%] h-[16%] bg-black/70" />
                  <span className="absolute left-[7%] right-[7%] top-[38%] text-[clamp(9px,2.6cqw,13px)] leading-snug">
                    <span className="block text-white/60">Your own account number</span>
                    <span className="block font-display font-semibold tracking-[0.12em] text-[clamp(12px,4cqw,20px)] mt-1">5566 3993 79</span>
                    <span className="block text-white/60 mt-[6%]">Freeze it or unfreeze it in one tap.</span>
                  </span>
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
      <p className="text-center text-xs text-[var(--lp-muted)] mt-3">Move over the card to tilt it. Tap to flip.</p>
    </div>
  );
}
