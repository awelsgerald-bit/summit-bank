import { useRef, useState } from 'react';
import { Camera, Moon, Sun, Trash2 } from 'lucide-react';
import api from '../api/client';
import Avatar from '../components/Avatar';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { errorMessage } from '../utils/errors';

const MAX_PICK_BYTES = 8 * 1024 * 1024;

// Shrinks the chosen picture to a 256x256 JPEG in the browser, so the upload stays tiny.
function resizeToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const size = 256;
      const canvas = document.createElement('canvas');
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext('2d');
      const side = Math.min(img.width, img.height);
      ctx.drawImage(img, (img.width - side) / 2, (img.height - side) / 2, side, side, 0, 0, size, size);
      URL.revokeObjectURL(url);
      resolve(canvas.toDataURL('image/jpeg', 0.85));
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('unreadable'));
    };
    img.src = url;
  });
}

function Message({ note }) {
  if (!note) return null;
  const good = note.type === 'ok';
  return (
    <div
      className="text-sm rounded-xl px-4 py-3 border"
      style={{
        color: good ? 'var(--success)' : 'var(--danger)',
        background: good ? 'rgba(52,211,153,0.1)' : 'rgba(251,113,133,0.1)',
        borderColor: good ? 'rgba(52,211,153,0.25)' : 'rgba(251,113,133,0.25)',
      }}
    >
      {note.text}
    </div>
  );
}

export default function Settings() {
  const { user, refreshProfile } = useAuth();
  const { theme, setTheme } = useTheme();
  const fileRef = useRef(null);

  const [name, setName] = useState(user?.full_name || '');
  const [phone, setPhone] = useState(user?.phone_number || '');
  const [profileNote, setProfileNote] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);

  const [photoNote, setPhotoNote] = useState(null);
  const [photoBusy, setPhotoBusy] = useState(false);

  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [again, setAgain] = useState('');
  const [pwNote, setPwNote] = useState(null);
  const [savingPw, setSavingPw] = useState(false);

  async function saveProfile(e) {
    e.preventDefault();
    setProfileNote(null);
    setSavingProfile(true);
    try {
      await api.patch('/account/profile', { full_name: name.trim(), phone_number: phone.trim() });
      await refreshProfile();
      setProfileNote({ type: 'ok', text: 'Profile updated.' });
    } catch (err) {
      setProfileNote({ type: 'error', text: errorMessage(err, 'Could not update your profile.') });
    } finally {
      setSavingProfile(false);
    }
  }

  async function pickPhoto(e) {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setPhotoNote(null);
    if (!file.type.startsWith('image/') || file.size > MAX_PICK_BYTES) {
      setPhotoNote({ type: 'error', text: 'Choose a picture smaller than 8 MB.' });
      return;
    }
    setPhotoBusy(true);
    try {
      const image = await resizeToDataUrl(file);
      await api.put('/account/avatar', { image });
      await refreshProfile();
      setPhotoNote({ type: 'ok', text: 'Profile photo updated.' });
    } catch (err) {
      setPhotoNote({ type: 'error', text: errorMessage(err, 'Could not use that picture.') });
    } finally {
      setPhotoBusy(false);
    }
  }

  async function removePhoto() {
    setPhotoNote(null);
    setPhotoBusy(true);
    try {
      await api.delete('/account/avatar');
      await refreshProfile();
      setPhotoNote({ type: 'ok', text: 'Profile photo removed.' });
    } catch (err) {
      setPhotoNote({ type: 'error', text: errorMessage(err, 'Could not remove the photo.') });
    } finally {
      setPhotoBusy(false);
    }
  }

  async function changePassword(e) {
    e.preventDefault();
    setPwNote(null);
    if (next.length < 8) {
      setPwNote({ type: 'error', text: 'The new password must be at least 8 characters.' });
      return;
    }
    if (next !== again) {
      setPwNote({ type: 'error', text: 'The two new passwords do not match.' });
      return;
    }
    setSavingPw(true);
    try {
      await api.post('/account/change-password', { current_password: current, new_password: next });
      setCurrent('');
      setNext('');
      setAgain('');
      setPwNote({ type: 'ok', text: 'Password changed.' });
    } catch (err) {
      setPwNote({ type: 'error', text: errorMessage(err, 'Could not change your password.') });
    } finally {
      setSavingPw(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-5 stagger">
      <h2 className="font-display text-lg font-medium">Settings</h2>

      <section className="glass rounded-3xl p-6 space-y-4">
        <h3 className="font-display text-sm text-[var(--text-2)]">Appearance</h3>
        <div className="flex gap-2">
          {[
            { id: 'dark', label: 'Dark', icon: Moon },
            { id: 'light', label: 'Light', icon: Sun },
          ].map((o) => (
            <button
              key={o.id}
              onClick={() => setTheme(o.id)}
              className={`flex-1 rounded-full py-2.5 text-sm flex items-center justify-center gap-2 toggle-pill ${
                theme === o.id ? 'toggle-active' : 'text-[var(--text-2)]'
              }`}
            >
              <o.icon size={15} /> {o.label}
            </button>
          ))}
        </div>
      </section>

      <section className="glass rounded-3xl p-6 space-y-4">
        <h3 className="font-display text-sm text-[var(--text-2)]">Profile photo</h3>
        <div className="flex items-center gap-4">
          <Avatar user={user} size={72} />
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => fileRef.current?.click()}
              disabled={photoBusy}
              className="btn-primary rounded-full px-4 py-2 text-sm font-medium flex items-center gap-2"
            >
              <Camera size={15} /> {user?.avatar ? 'Change photo' : 'Add photo'}
            </button>
            {user?.avatar && (
              <button
                onClick={removePhoto}
                disabled={photoBusy}
                className="rounded-full px-4 py-2 text-sm border border-white/10 text-[var(--danger)] flex items-center gap-2"
              >
                <Trash2 size={15} /> Remove
              </button>
            )}
          </div>
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={pickPhoto} />
        </div>
        <Message note={photoNote} />
      </section>

      <form onSubmit={saveProfile} className="glass rounded-3xl p-6 space-y-4">
        <h3 className="font-display text-sm text-[var(--text-2)]">Personal details</h3>
        <label className="block text-xs text-[var(--text-3)]">
          Full name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            minLength={2}
            maxLength={150}
            required
            className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm text-[var(--text-1)] bg-transparent outline-none"
          />
        </label>
        <label className="block text-xs text-[var(--text-3)]">
          Phone number
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            inputMode="tel"
            minLength={10}
            maxLength={20}
            required
            className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm text-[var(--text-1)] bg-transparent outline-none"
          />
        </label>
        <p className="text-xs text-[var(--text-3)]">
          Email: {user?.email}. Your email and account number can't be changed here.
        </p>
        <Message note={profileNote} />
        <button disabled={savingProfile} className="btn-primary rounded-full px-5 py-2.5 text-sm font-medium">
          {savingProfile ? 'Saving...' : 'Save changes'}
        </button>
      </form>

      <form onSubmit={changePassword} className="glass rounded-3xl p-6 space-y-4">
        <h3 className="font-display text-sm text-[var(--text-2)]">Change password</h3>
        {[
          ['Current password', current, setCurrent, 'current-password'],
          ['New password', next, setNext, 'new-password'],
          ['Repeat new password', again, setAgain, 'new-password'],
        ].map(([label, value, setter, auto]) => (
          <label key={label} className="block text-xs text-[var(--text-3)]">
            {label}
            <input
              type="password"
              value={value}
              onChange={(e) => setter(e.target.value)}
              autoComplete={auto}
              required
              className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm text-[var(--text-1)] bg-transparent outline-none"
            />
          </label>
        ))}
        <Message note={pwNote} />
        <button disabled={savingPw} className="btn-primary rounded-full px-5 py-2.5 text-sm font-medium">
          {savingPw ? 'Changing...' : 'Change password'}
        </button>
      </form>
    </div>
  );
}
