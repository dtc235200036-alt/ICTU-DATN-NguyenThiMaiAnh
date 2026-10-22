import { useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
import '@fontsource/be-vietnam-pro/400.css'
import '@fontsource/be-vietnam-pro/500.css'
import '@fontsource/be-vietnam-pro/600.css'
import '@fontsource/be-vietnam-pro/700.css'

import logoIctu from '../../assets/logo-ictu.png'
import './LandingPage.css'

gsap.registerPlugin(ScrollTrigger, useGSAP)

const MARQUEE = [
  'Giao đề tài',
  'Nộp đề cương',
  'Kiểm tra tên file',
  'Kiểm tra định hướng',
  'Ký số PDF',
  'Báo cáo tiến độ',
  'Kiểm tra trùng lặp',
  'Hội đồng bảo vệ',
  'Kho đồ án',
]

const STEPS: { title: string; text: string; who: string }[] = [
  {
    who: 'Sinh viên',
    title: 'Nộp đề cương đúng mẫu',
    text: 'Tải file PDF hoặc DOCX đặt tên theo mẫu Hxx.MSSV.Họ tên.Lớp, kèm ghi chú gửi GVHD. Hệ thống chạy kiểm tra trùng lặp ngay sau khi nộp.',
  },
  {
    who: 'GVHD',
    title: 'Xem trước và duyệt',
    text: 'Đọc file ngay trên trình duyệt, xem kết quả kiểm tra tên file, định hướng và nội dung, rồi duyệt hoặc yêu cầu sửa.',
  },
  {
    who: 'GVHD',
    title: 'Nộp lên Bộ môn',
    text: 'Đề cương đã duyệt được nộp lên Bộ môn bằng một nút. Bộ môn và sinh viên nhận thông báo cùng lúc.',
  },
  {
    who: 'Lãnh đạo bộ môn',
    title: 'Phê duyệt bằng chữ ký số',
    text: 'Tải lên bản PDF đã ký. Hệ thống đọc chữ ký, kiểm tra chữ ký phủ toàn bộ file rồi mới chấp nhận.',
  },
  {
    who: 'Khoa',
    title: 'Lưu và xuất về khoa',
    text: 'Các bản đã ký được lưu theo đợt và tải về thành một file ZIP, sẵn sàng nộp về khoa.',
  },
]

const ROLES: { key: string; name: string; tone: string; glyph: string; items: string[] }[] = [
  {
    key: 'sv',
    name: 'Sinh viên',
    tone: 'blue',
    glyph: 'M12 4l9 4-9 4-9-4z M7 10v5c0 1.5 2.2 3 5 3s5-1.5 5-3v-5',
    items: [
      'Xem đề tài được giao và GVHD',
      'Nộp đề cương, báo cáo tiến độ, báo cáo cuối',
      'Theo dõi trạng thái duyệt từng bước',
      'Xem lịch và kết quả bảo vệ',
    ],
  },
  {
    key: 'gv',
    name: 'Giảng viên hướng dẫn',
    tone: 'cyan',
    glyph: 'M4 5h16v11H4z M9 20h6 M12 16v4',
    items: [
      'Giao đề tài theo định hướng của Bộ môn',
      'Duyệt đề cương, nộp lên Bộ môn',
      'Theo dõi tiến độ sinh viên theo mốc',
      'Chấm điểm trong hội đồng bảo vệ',
    ],
  },
  {
    key: 'bm',
    name: 'Bộ môn',
    tone: 'amber',
    glyph: 'M4 20h16 M6 20V10 M10 20V10 M14 20V10 M18 20V10 M3 10l9-6 9 6z',
    items: [
      'Phân công GVHD, quản lý đợt đồ án',
      'Phê duyệt đề cương bằng chữ ký số',
      'Cấu hình ngưỡng cảnh báo trùng lặp',
      'Lập hội đồng, chốt điểm, quản lý kho đồ án',
    ],
  },
]

const REVEAL_TEXT =
  'Mỗi đề cương đi qua hai cấp duyệt. Mỗi file được kiểm tra tên, định hướng và nội dung. Mỗi chữ ký số được đọc lại trước khi lưu về khoa. Không còn chuyển file qua email hay in ra để ký.'

function Icon({ d, size = 22 }: { d: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d={d} />
    </svg>
  )
}

const ICON_CHECK = 'M5 12.5l4.5 4.5L19 7.5'
const ICON_ARROW = 'M5 12h14 M13 6l6 6-6 6'

function Nav() {
  return (
    <header className="lp-nav">
      <Link to="/" className="lp-nav__brand" aria-label="Trang giới thiệu">
        <img src={logoIctu} alt="" />
        <span>Đồ án tốt nghiệp</span>
      </Link>
      <nav className="lp-nav__links" aria-label="Mục trên trang">
        <a href="#tinh-nang">Tính năng</a>
        <a href="#quy-trinh">Quy trình</a>
        <a href="#vai-tro">Vai trò</a>
      </nav>
      <Link to="/dang-nhap" className="lp-btn lp-btn--light lp-btn--sm">
        Đăng nhập
      </Link>
    </header>
  )
}

/** Cửa sổ ứng dụng dựng bằng CSS — dữ liệu minh họa, không phải dữ liệu thật. */
function AppWindow() {
  const rows: { name: string; topic: string; tag: string; tone: string }[] = [
    { name: 'Nguyễn Văn A', topic: 'Hệ thống điểm danh bằng nhận diện khuôn mặt', tag: 'Chờ Bộ môn duyệt', tone: 'amber' },
    { name: 'Trần Thị B', topic: 'Ứng dụng quản lý thư viện trên nền tảng web', tag: 'GVHD đã duyệt', tone: 'cyan' },
    { name: 'Lê Văn C', topic: 'Chatbot hỗ trợ tuyển sinh dùng mô hình ngôn ngữ', tag: 'Đã duyệt', tone: 'green' },
    { name: 'Phạm Thị D', topic: 'Website thương mại điện tử cho cửa hàng nông sản', tag: 'Yêu cầu sửa', tone: 'red' },
  ]
  return (
    <div className="lp-window" aria-hidden>
      <div className="lp-window__bar">
        <i />
        <i />
        <i />
        <span>Duyệt đề cương</span>
      </div>
      <div className="lp-window__body">
        <aside className="lp-window__side">
          {['Tổng quan', 'Đề tài', 'Duyệt đề cương', 'Tiến độ', 'Bảo vệ', 'Kho đồ án'].map((m, i) => (
            <div key={m} className={i === 2 ? 'is-active' : undefined}>
              {m}
            </div>
          ))}
        </aside>
        <div className="lp-window__main">
          <div className="lp-window__tabs">
            <span className="is-active">Chờ duyệt</span>
            <span>Đã duyệt</span>
            <span>Bộ môn trả lại</span>
          </div>
          {rows.map((r, i) => (
            <div key={r.name} className="lp-window__row">
              <span className="lp-window__stt">{i + 1}</span>
              <span className="lp-window__name">{r.name}</span>
              <span className="lp-window__topic">{r.topic}</span>
              <span className={`lp-tag lp-tag--${r.tone}`}>{r.tag}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Hero() {
  return (
    <section className="lp-hero">
      <div className="lp-hero__mesh" aria-hidden />
      <div className="lp-wrap lp-hero__inner">
        <h1 className="lp-hero__title">
          Đồ án tốt nghiệp
          <span className="lp-inline-img" aria-hidden>
            <img src={logoIctu} alt="" />
          </span>
          từ lúc giao đề tài đến ngày bảo vệ, trên một hệ thống
        </h1>
        <p className="lp-hero__lead">
          Sinh viên, giảng viên hướng dẫn và Bộ môn Khoa Công nghệ thông tin ICTU cùng làm việc
          trên một quy trình: giao đề tài, duyệt đề cương hai cấp có ký số, theo dõi tiến độ và
          kiểm tra trùng lặp bằng AI.
        </p>
        <div className="lp-hero__cta">
          <Link to="/dang-nhap" className="lp-btn lp-btn--light">
            Đăng nhập hệ thống
            <Icon d={ICON_ARROW} size={18} />
          </Link>
          <a href="#quy-trinh" className="lp-btn lp-btn--ghost">
            Xem quy trình duyệt
          </a>
        </div>
      </div>
      <div className="lp-wrap lp-hero__visual">
        <div className="lp-scale-in">
          <AppWindow />
        </div>
      </div>
    </section>
  )
}

function Marquee() {
  const items = [...MARQUEE, ...MARQUEE]
  return (
    <div className="lp-marquee" aria-hidden>
      <div className="lp-marquee__track">
        {items.map((t, i) => (
          <span key={i}>
            {t}
            <i />
          </span>
        ))}
      </div>
    </div>
  )
}

function SimilarityVisual() {
  const bars: { label: string; value: number; tone: string }[] = [
    { label: 'Ngữ nghĩa tên đề tài', value: 82, tone: 'red' },
    { label: 'Nội dung đề cương', value: 41, tone: 'amber' },
    { label: 'Trùng nguyên văn', value: 12, tone: 'green' },
  ]
  return (
    <div className="lp-sim" aria-hidden>
      {bars.map((b) => (
        <div key={b.label} className="lp-sim__row">
          <div className="lp-sim__label">
            <span>{b.label}</span>
            <b>{b.value}%</b>
          </div>
          <div className="lp-sim__track">
            <div className={`lp-sim__fill lp-sim__fill--${b.tone}`} style={{ width: `${b.value}%` }} />
            <div className="lp-sim__threshold" />
          </div>
        </div>
      ))}
      <div className="lp-sim__note">Vạch trắng: ngưỡng cảnh báo do Bộ môn cấu hình</div>
    </div>
  )
}

function BentoCard({
  className,
  title,
  text,
  children,
}: {
  className: string
  title: string
  text: string
  children: ReactNode
}) {
  return (
    <article className={`lp-card ${className}`}>
      <div className="lp-card__visual">{children}</div>
      <div className="lp-card__copy">
        <h3>{title}</h3>
        <p>{text}</p>
      </div>
    </article>
  )
}

function Bento() {
  return (
    <section id="tinh-nang" className="lp-section lp-section--dark">
      <div className="lp-wrap">
        <h2 className="lp-h2 lp-fade-up">Mọi bước của đồ án nằm trên cùng một hệ thống</h2>
        <div className="lp-bento">
          <BentoCard
            className="lp-card--hero"
            title="Kiểm tra trùng lặp bằng AI"
            text="So sánh ngữ nghĩa tên đề tài bằng mô hình nhúng tiếng Việt và dò trùng nguyên văn bằng vân tay cụm âm tiết, đối chiếu với kho đồ án của khoa."
          >
            <SimilarityVisual />
          </BentoCard>
          <BentoCard
            className="lp-card--sign"
            title="Chữ ký số được kiểm tra"
            text="Đọc người ký, thời điểm ký và xác nhận chữ ký phủ toàn bộ file PDF."
          >
            <div className="lp-sign" aria-hidden>
              <span className="lp-sign__seal">
                <Icon d={ICON_CHECK} size={28} />
              </span>
              <div>
                <b>Đã ký số</b>
                <span>Chữ ký phủ toàn bộ file</span>
              </div>
            </div>
          </BentoCard>
          <BentoCard
            className="lp-card--progress"
            title="Tiến độ theo mốc"
            text="Mỗi mốc có hạn nộp; nộp trễ hay quá hạn đều hiện rõ cho GVHD."
          >
            <div className="lp-steps" aria-hidden>
              {['done', 'done', 'late', 'todo'].map((s, i) => (
                <span key={i} className={`lp-steps__dot lp-steps__dot--${s}`}>
                  {i + 1}
                </span>
              ))}
            </div>
          </BentoCard>
          <BentoCard
            className="lp-card--wide"
            title="Từ hội đồng bảo vệ đến kho đồ án"
            text="Bộ môn lập hội đồng, xếp lịch, chốt điểm; đồ án đã bảo vệ được lưu vào kho để các khóa sau tra cứu và làm dữ liệu đối chiếu trùng lặp."
          >
            <div className="lp-chips" aria-hidden>
              {['Hội đồng 01 · Phòng C3.201', '08:00 · Thứ Hai', 'Chủ tịch · Thư ký · Ủy viên', 'Kho đồ án các khóa'].map(
                (c) => (
                  <span key={c}>{c}</span>
                ),
              )}
            </div>
          </BentoCard>
        </div>
      </div>
    </section>
  )
}

function Process() {
  return (
    <section id="quy-trinh" className="lp-section lp-section--light lp-process">
      <div className="lp-wrap lp-process__grid">
        <div className="lp-process__pin">
          <h2 className="lp-h2">Duyệt đề cương hai cấp, không cần in ra để ký</h2>
          <p className="lp-process__lead">
            Đề cương đi từ sinh viên đến GVHD, rồi lên Lãnh đạo bộ môn. Mỗi bước để lại lịch sử,
            mỗi lần trả lại có nhận xét.
          </p>
          <div className="lp-process__meter" aria-hidden>
            <div className="lp-process__meter-fill" />
          </div>
        </div>
        <ol className="lp-process__list">
          {STEPS.map((s, i) => (
            <li key={s.title} className="lp-step">
              <span className="lp-step__num">{String(i + 1).padStart(2, '0')}</span>
              <div>
                <span className="lp-step__who">{s.who}</span>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}

function Reveal() {
  return (
    <section className="lp-section lp-section--light lp-reveal">
      <div className="lp-wrap">
        <p className="lp-reveal__text">
          {REVEAL_TEXT.split(' ').map((w, i) => (
            <span key={i} className="lp-word">
              {w}{' '}
            </span>
          ))}
        </p>
      </div>
    </section>
  )
}

function Roles() {
  const [active, setActive] = useState('gv')
  return (
    <section id="vai-tro" className="lp-section lp-section--dark">
      <div className="lp-wrap">
        <h2 className="lp-h2 lp-fade-up">Mỗi vai trò thấy đúng phần việc của mình</h2>
        <div className="lp-accordion">
          {ROLES.map((r) => (
            <button
              key={r.key}
              type="button"
              className={`lp-slice lp-slice--${r.tone}${active === r.key ? ' is-active' : ''}`}
              onMouseEnter={() => setActive(r.key)}
              onFocus={() => setActive(r.key)}
              onClick={() => setActive(r.key)}
              aria-expanded={active === r.key}
            >
              <span className="lp-slice__name">{r.name}</span>
              <span className="lp-slice__glyph" aria-hidden>
                <Icon d={r.glyph} size={26} />
              </span>
              <ul className="lp-slice__items">
                {r.items.map((it) => (
                  <li key={it}>
                    <Icon d={ICON_CHECK} size={16} />
                    {it}
                  </li>
                ))}
              </ul>
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}

function Cta() {
  return (
    <section className="lp-cta">
      <div className="lp-hero__mesh lp-hero__mesh--cta" aria-hidden />
      <div className="lp-wrap lp-cta__inner">
        <h2 className="lp-cta__title">Vào hệ thống bằng tài khoản do Bộ môn cấp</h2>
        <Link to="/dang-nhap" className="lp-btn lp-btn--light lp-btn--lg">
          Đăng nhập
          <Icon d={ICON_ARROW} size={20} />
        </Link>
      </div>
      <footer className="lp-wrap lp-footer">
        <div className="lp-footer__brand">
          <img src={logoIctu} alt="Logo ICTU" />
          <div>
            Trường ĐH Công nghệ Thông tin và Truyền thông
            <br />
            Khoa Công nghệ thông tin
          </div>
        </div>
        <nav className="lp-footer__links" aria-label="Liên kết cuối trang">
          <a href="#tinh-nang">Tính năng</a>
          <a href="#quy-trinh">Quy trình</a>
          <a href="#vai-tro">Vai trò</a>
          <Link to="/dang-nhap">Đăng nhập</Link>
        </nav>
        <div className="lp-footer__copy">© {new Date().getFullYear()} Khoa CNTT — ICTU</div>
      </footer>
    </section>
  )
}

/**
 * Trang giới thiệu công khai ở "/": hero, tính năng (bento), quy trình duyệt
 * hai cấp (ghim khi cuộn), vai trò, kêu gọi đăng nhập. Hiệu ứng cuộn chỉ bật
 * khi người dùng không yêu cầu giảm chuyển động.
 */
export default function LandingPage() {
  const root = useRef<HTMLElement>(null)

  useGSAP(
    () => {
      const mm = gsap.matchMedia()

      mm.add('(prefers-reduced-motion: no-preference)', () => {
        gsap.from('.lp-hero__title, .lp-hero__lead, .lp-hero__cta', {
          y: 32,
          opacity: 0,
          duration: 1,
          ease: 'power3.out',
          stagger: 0.12,
        })

        // Cửa sổ ứng dụng: nhỏ -> đầy đủ khi cuộn vào, tối dần khi cuộn qua.
        gsap.fromTo(
          '.lp-scale-in',
          { scale: 0.82, opacity: 0.6 },
          {
            scale: 1,
            opacity: 1,
            ease: 'none',
            scrollTrigger: { trigger: '.lp-hero__visual', start: 'top 95%', end: 'top 35%', scrub: true },
          },
        )
        gsap.to('.lp-scale-in', {
          opacity: 0.2,
          ease: 'none',
          scrollTrigger: { trigger: '.lp-hero__visual', start: 'bottom 55%', end: 'bottom 5%', scrub: true },
        })

        gsap.utils.toArray<HTMLElement>('.lp-fade-up, .lp-card').forEach((el) => {
          gsap.from(el, {
            y: 40,
            opacity: 0,
            duration: 0.9,
            ease: 'power3.out',
            scrollTrigger: { trigger: el, start: 'top 88%' },
          })
        })

        // Từng chữ của đoạn văn sáng dần theo cuộn.
        gsap.fromTo(
          '.lp-word',
          { opacity: 0.12 },
          {
            opacity: 1,
            stagger: 0.1,
            ease: 'none',
            scrollTrigger: { trigger: '.lp-reveal', start: 'top 75%', end: 'bottom 60%', scrub: true },
          },
        )
      })

      // Ghim tiêu đề quy trình bên trái khi các bước cuộn bên phải (chỉ màn rộng).
      mm.add('(prefers-reduced-motion: no-preference) and (min-width: 960px)', () => {
        const pin = root.current?.querySelector<HTMLElement>('.lp-process__pin')
        const list = root.current?.querySelector<HTMLElement>('.lp-process__list')
        if (pin && list) {
          // Ghim tới khi đáy cột trái chạm đáy danh sách bước.
          ScrollTrigger.create({
            trigger: '.lp-process__grid',
            start: 'top 120px',
            end: () => `+=${Math.max(0, list.offsetHeight - pin.offsetHeight)}`,
            pin,
            pinSpacing: false,
            invalidateOnRefresh: true,
          })
        }
        gsap.fromTo(
          '.lp-process__meter-fill',
          { scaleY: 0 },
          {
            scaleY: 1,
            ease: 'none',
            scrollTrigger: { trigger: '.lp-process__list', start: 'top 70%', end: 'bottom 70%', scrub: true },
          },
        )
        gsap.utils.toArray<HTMLElement>('.lp-step').forEach((el) => {
          gsap.from(el, {
            x: 48,
            opacity: 0,
            duration: 0.8,
            ease: 'power3.out',
            scrollTrigger: { trigger: el, start: 'top 85%' },
          })
        })
      })
    },
    { scope: root },
  )

  return (
    <main ref={root} className="lp">
      <Nav />
      <Hero />
      <Marquee />
      <Bento />
      <Process />
      <Reveal />
      <Roles />
      <Cta />
    </main>
  )
}
