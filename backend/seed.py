"""Auto-seed realistic IU data on first run if DB is empty."""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from models import Student, Event, Attendance, EventCode

# Points per event follow this cycle (index % 10): 50,10,25,30,15,40,20,35,5,45
POINTS_CYCLE = [50, 10, 25, 30, 15, 40, 20, 35, 5, 45]


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def seed_data(db: Session):
    if db.query(Student).count() > 0:
        return

    now = utcnow()
    days_since_sunday = (now.weekday() + 1) % 7
    week_start = (now - timedelta(days=days_since_sunday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # ── Events (realistic IU events across all campuses) ─────────────────────
    # points= values come from POINTS_CYCLE[index % 10]
    events = [
        Event(                                           # index 0 → 50 pts
            title="Luddy School AI & Innovation Summit",
            category="Tech",
            description=(
                "Join Luddy School faculty, students, and industry partners to explore "
                "the future of artificial intelligence, human-computer interaction, and "
                "data science. Keynotes, panels, and live demos."
            ),
            campus="IU Bloomington",
            event_url="https://luddy.indiana.edu/events",
            check_in_code="LUDDY2025",
            points=50,
            event_date=week_start + timedelta(days=1, hours=9),
        ),
        Event(                                           # index 1 → 10 pts
            title="IU Kelley Business Career Expo",
            category="Career",
            description=(
                "Connect with 80+ employers from finance, consulting, marketing, "
                "and tech. Bring copies of your resume. Business professional attire required."
            ),
            campus="IU Bloomington",
            event_url="https://kelley.iu.edu/events",
            check_in_code="KELLEY25",
            points=10,
            event_date=week_start + timedelta(days=1, hours=13),
        ),
        Event(                                           # index 2 → 25 pts
            title="IUPUI Research Showcase",
            category="Academic",
            description=(
                "Graduate and undergraduate students from IUPUI present their research "
                "across disciplines including medicine, engineering, liberal arts, and STEM. "
                "Open to all IU community members."
            ),
            campus="IU Indianapolis",
            event_url="https://research.iu.edu/events",
            check_in_code="IUPUIRC5",
            points=25,
            event_date=week_start + timedelta(days=2, hours=10),
        ),
        Event(                                           # index 3 → 30 pts
            title="Wellness & Mental Health Workshop",
            category="Health",
            description=(
                "IU Health Center hosts an interactive workshop on stress management, "
                "mindfulness techniques, and building resilience. Free snacks provided."
            ),
            campus="IU Bloomington",
            event_url="https://healthcenter.iu.edu",
            check_in_code="WELLNS25",
            points=30,
            event_date=week_start + timedelta(days=2, hours=14),
        ),
        Event(                                           # index 4 → 15 pts
            title="IU East STEM Networking Night",
            category="Career",
            description=(
                "Students from computer science, biology, chemistry, and math connect "
                "with regional employers. Hosted at the IU East Science Building atrium."
            ),
            campus="IU East",
            event_url="https://iue.iu.edu/events",
            check_in_code="IUEAST25",
            points=15,
            event_date=week_start + timedelta(days=2, hours=17),
        ),
        Event(                                           # index 5 → 40 pts
            title="Luddy Hacks Hackathon Kickoff",
            category="Tech",
            description=(
                "Opening ceremony for the 24-hour Luddy Hacks hackathon. Team formation, "
                "sponsor introductions, project pitches, and dinner. All skill levels welcome."
            ),
            campus="IU Bloomington",
            event_url="https://iuhacks.io",
            check_in_code="LHACKS25",
            points=40,
            event_date=week_start + timedelta(days=3, hours=9),
        ),
        Event(                                           # index 6 → 20 pts
            title="IU South Bend Arts & Culture Fair",
            category="Cultural",
            description=(
                "Celebrating diversity through art, music, dance, and cultural performances "
                "by student organizations. Includes food trucks and vendor booths."
            ),
            campus="IU South Bend",
            event_url="https://iusb.edu/events",
            check_in_code="SBARTS5",
            points=20,
            event_date=week_start + timedelta(days=3, hours=12),
        ),
        Event(                                           # index 7 → 35 pts
            title="IU Kokomo Entrepreneurship Pitch Night",
            category="Career",
            description=(
                "Students pitch startup ideas to a panel of local investors and IU faculty. "
                "Top three teams win seed funding and mentorship opportunities."
            ),
            campus="IU Kokomo",
            event_url="https://iuk.iu.edu/events",
            check_in_code="KOKOPIT5",
            points=35,
            event_date=week_start + timedelta(days=3, hours=18),
        ),
        Event(                                           # index 8 → 5 pts
            title="IU Northwest Community Leadership Forum",
            category="Social",
            description=(
                "Panel discussion with community leaders, IU faculty, and students on "
                "civic engagement, public policy, and social impact in Northwest Indiana."
            ),
            campus="IU Northwest",
            event_url="https://iun.iu.edu/events",
            check_in_code="NWLEAD5",
            points=5,
            event_date=week_start + timedelta(days=4, hours=11),
        ),
        Event(                                           # index 9 → 45 pts
            title="IU Southeast Tech & Coding Bootcamp",
            category="Tech",
            description=(
                "A full-day intensive coding workshop covering Python, web development, "
                "and database fundamentals. Beginner-friendly with take-home projects."
            ),
            campus="IU Southeast",
            event_url="https://ius.iu.edu/events",
            check_in_code="SECODE5",
            points=45,
            event_date=week_start + timedelta(days=4, hours=9),
        ),
        Event(                                           # index 10 → 50 pts
            title="IU Columbus Diversity & Inclusion Summit",
            category="Cultural",
            description=(
                "Annual summit featuring keynote speakers, workshops, and panel discussions "
                "celebrating diversity, equity, and inclusion across the IU system."
            ),
            campus="IU Columbus",
            event_url="https://iuc.iu.edu/events",
            check_in_code="IUCDIV5",
            points=50,
            event_date=week_start + timedelta(days=4, hours=13),
        ),
        Event(                                           # index 11 → 10 pts
            title="IU Fort Wayne Engineering Design Expo",
            category="Academic",
            description=(
                "Engineering students showcase their senior capstone projects. "
                "Judges from industry evaluate designs for innovation, feasibility, and impact."
            ),
            campus="IU Fort Wayne",
            event_url="https://iufw.iu.edu/events",
            check_in_code="FWEXPO5",
            points=10,
            event_date=week_start + timedelta(days=5, hours=10),
        ),
        Event(                                           # index 12 → 25 pts
            title="Maurer School of Law Mock Trial",
            category="Academic",
            description=(
                "Pre-law and law students argue a simulated civil case before a panel of "
                "practicing attorneys and alumni judges. Open for observation."
            ),
            campus="IU Bloomington",
            event_url="https://law.indiana.edu/events",
            check_in_code="LAWMOCK5",
            points=25,
            event_date=week_start + timedelta(days=5, hours=14),
        ),
        Event(                                           # index 13 → 30 pts
            title="IU Indianapolis Health Sciences Symposium",
            category="Health",
            description=(
                "Medical, nursing, and public health students present research posters "
                "and case studies. Sponsored by IU School of Medicine and IUPUI Health."
            ),
            campus="IU Indianapolis",
            event_url="https://medicine.iu.edu/events",
            check_in_code="HEALTH25",
            points=30,
            event_date=week_start + timedelta(days=5, hours=9),
        ),
        Event(                                           # index 14 → 15 pts
            title="IU Sustainability & Green Campus Expo",
            description=(
                "Learn about IU's carbon neutrality goals, sustainability initiatives, "
                "and how students can get involved. Features electric vehicle demos and recycling drives."
            ),
            category="Social",
            campus="IU Bloomington",
            event_url="https://sustain.indiana.edu",
            check_in_code="GREEN25",
            points=15,
            event_date=week_start + timedelta(days=6, hours=11),
        ),
        # ── 32 additional events spread over next 30 days ────────────────────
        Event(                                           # index 15 → 40 pts
            title="Little 500 Kickoff Party",
            category="Sports",
            description=(
                "Celebrate the start of Indiana's iconic Little 500 bicycle race weekend with "
                "live music, food trucks, and campus spirit activities. The Little 500 is the "
                "world's largest collegiate bike race — don't miss the kickoff bash!"
            ),
            campus="IU Bloomington",
            event_url="https://iusf.indiana.edu/l500/index.html",
            check_in_code="LITTLE500",
            points=40,
            event_date=now + timedelta(days=1, hours=16),
        ),
        Event(                                           # index 16 → 20 pts
            title="IU Career Fair: STEM Edition",
            category="Career",
            description=(
                "Connect with 60+ top employers recruiting for engineering, data science, "
                "cybersecurity, and research roles. Bring your resume and IU ID. Companies "
                "include Google, Salesforce, Eli Lilly, Cummins, and more."
            ),
            campus="IU Bloomington",
            event_url="https://careers.indiana.edu/channels/career-fairs/index.html",
            check_in_code="STEMFAIR",
            points=20,
            event_date=now + timedelta(days=2, hours=10),
        ),
        Event(                                           # index 17 → 35 pts
            title="Lotus World Music & Arts Festival",
            category="Cultural",
            description=(
                "Bloomington's celebrated annual world music festival returns with artists from "
                "over 20 countries performing across downtown venues and the IU campus. "
                "Free student admission with valid IU ID."
            ),
            campus="IU Bloomington",
            event_url="https://lotusfest.org",
            check_in_code="LOTUS25",
            points=35,
            event_date=now + timedelta(days=3, hours=14),
        ),
        Event(                                           # index 18 → 5 pts
            title="Undergraduate Research Symposium",
            category="Academic",
            description=(
                "IU's premier undergraduate research showcase featuring 200+ student poster "
                "presentations across science, humanities, and social sciences. Meet faculty "
                "mentors and learn about research opportunities at IU."
            ),
            campus="IU Bloomington",
            event_url="https://research.indiana.edu/undergraduate/index.html",
            check_in_code="UGRSYMP5",
            points=5,
            event_date=now + timedelta(days=4, hours=9),
        ),
        Event(                                           # index 19 → 45 pts
            title="IU Basketball Watch Party",
            category="Sports",
            description=(
                "Watch the Hoosiers live on the big screen at Alumni Hall with fellow fans. "
                "Free popcorn and drinks for the first 200 attendees. Wear your cream and "
                "crimson — the bigger the crowd, the louder the roar!"
            ),
            campus="IU Bloomington",
            event_url="https://iuhoosiers.com/sports/mens-basketball",
            check_in_code="BBALL25",
            points=45,
            event_date=now + timedelta(days=4, hours=19),
        ),
        Event(                                           # index 20 → 50 pts
            title="Study Abroad Information Fair",
            category="Academic",
            description=(
                "Explore 200+ IU study abroad programs across 50+ countries. Chat with "
                "program advisors, returned students, and international partners. Learn about "
                "scholarships, credit transfers, and application deadlines."
            ),
            campus="IU Bloomington",
            event_url="https://overseas.iu.edu/index.html",
            check_in_code="STUDYAB5",
            points=50,
            event_date=now + timedelta(days=5, hours=11),
        ),
        Event(                                           # index 21 → 10 pts
            title="Kelley Consulting Case Competition",
            category="Career",
            description=(
                "Test your business acumen in this live case competition sponsored by Kelley "
                "School of Business alumni. Teams of 3 have 30 minutes to analyze and present "
                "a real business problem. Top prizes include internship opportunities."
            ),
            campus="IU Bloomington",
            event_url="https://kelley.iu.edu/programs/undergrad/student-life/competitions.html",
            check_in_code="KELCASE5",
            points=10,
            event_date=now + timedelta(days=6, hours=9),
        ),
        Event(                                           # index 22 → 25 pts
            title="Data Science & ML Workshop",
            category="Tech",
            description=(
                "Hands-on workshop covering Python machine learning with scikit-learn and "
                "PyTorch. Build your first neural network, learn feature engineering, and "
                "explore real IU datasets. Laptops required — all skill levels welcome."
            ),
            campus="IU Bloomington",
            event_url="https://luddy.indiana.edu/news-events/events/index.html",
            check_in_code="DATASCI5",
            points=25,
            event_date=now + timedelta(days=7, hours=13),
        ),
        Event(                                           # index 23 → 30 pts
            title="Latino Heritage Month Celebration",
            category="Cultural",
            description=(
                "Celebrate Latino culture with live performances of salsa, cumbia, and mariachi, "
                "traditional food from across Latin America, and art displays by IU Indianapolis "
                "student artists. Co-sponsored by IUPUI's Latino Cultural Center."
            ),
            campus="IU Indianapolis",
            event_url="https://diversity.iupui.edu/centers/latino/events.html",
            check_in_code="LATINO25",
            points=30,
            event_date=now + timedelta(days=8, hours=17),
        ),
        Event(                                           # index 24 → 15 pts
            title="IU Day of Service: Community Volunteer",
            category="Social",
            description=(
                "Join hundreds of IU students volunteering across Indianapolis neighborhoods. "
                "Projects include park cleanups, food bank sorting, school painting, and senior "
                "center visits. All supplies provided — just bring your energy!"
            ),
            campus="IU Indianapolis",
            event_url="https://servicelearning.iupui.edu",
            check_in_code="DAYSERV5",
            points=15,
            event_date=now + timedelta(days=9, hours=8),
        ),
        Event(                                           # index 25 → 40 pts
            title="IU School of Medicine Open House",
            category="Academic",
            description=(
                "Pre-med students: tour the IU School of Medicine facilities, meet current "
                "medical students, and attend Q&A sessions with admissions officers. Learn "
                "about MD, MD-PhD, and dual-degree program requirements."
            ),
            campus="IU Indianapolis",
            event_url="https://medicine.iu.edu/admissions/events",
            check_in_code="MEDOPEN5",
            points=40,
            event_date=now + timedelta(days=10, hours=10),
        ),
        Event(                                           # index 26 → 20 pts
            title="Cybersecurity Awareness Workshop",
            category="Tech",
            description=(
                "Learn to protect yourself and your data with hands-on demos of phishing "
                "simulations, password managers, VPNs, and secure coding practices. "
                "Hosted by IUPUI's Center for Information Security Education."
            ),
            campus="IU Indianapolis",
            event_url="https://soic.iupui.edu/events",
            check_in_code="CYBER25",
            points=20,
            event_date=now + timedelta(days=11, hours=14),
        ),
        Event(                                           # index 27 → 35 pts
            title="IU East Community Art Exhibition",
            category="Cultural",
            description=(
                "Student and faculty artwork on display in the Whitewater Hall Gallery, "
                "featuring paintings, sculpture, photography, and digital media. "
                "Opening reception with light refreshments — free and open to the public."
            ),
            campus="IU East",
            event_url="https://east.indiana.edu/arts-humanities/index.html",
            check_in_code="IUEART5",
            points=35,
            event_date=now + timedelta(days=12, hours=12),
        ),
        Event(                                           # index 28 → 5 pts
            title="Financial Wellness Seminar",
            category="Health",
            description=(
                "Learn practical money skills: budgeting on a student income, understanding "
                "FAFSA and scholarships, building credit, and planning for student loan "
                "repayment. Free one-on-one advising slots available after the seminar."
            ),
            campus="IU East",
            event_url="https://east.indiana.edu/student-services/financial-aid/index.html",
            check_in_code="FINWEL5",
            points=5,
            event_date=now + timedelta(days=13, hours=15),
        ),
        Event(                                           # index 29 → 45 pts
            title="IU Kokomo Science Fair",
            category="Academic",
            description=(
                "Annual showcase of undergraduate STEM research at IU Kokomo. Student teams "
                "present original experiments and engineering projects judged by local industry "
                "professionals. Best-in-show receives a $500 research grant."
            ),
            campus="IU Kokomo",
            event_url="https://iuk.iu.edu/academics/stem/index.html",
            check_in_code="KOKSCI5",
            points=45,
            event_date=now + timedelta(days=14, hours=10),
        ),
        Event(                                           # index 30 → 50 pts
            title="Northwest Student Leadership Summit",
            category="Social",
            description=(
                "A full-day leadership development conference for IU Northwest students. "
                "Workshops on public speaking, team management, and campus advocacy. "
                "Keynote by a Northwest alumni now serving in state government."
            ),
            campus="IU Northwest",
            event_url="https://www.iun.edu/student-affairs/leadership.htm",
            check_in_code="NWSLS25",
            points=50,
            event_date=now + timedelta(days=15, hours=9),
        ),
        Event(                                           # index 31 → 10 pts
            title="South Bend Civic Engagement Forum",
            category="Social",
            description=(
                "Faculty, students, and South Bend city officials discuss how IU South Bend "
                "students can shape local policy on housing, transit, and economic development. "
                "Registration required — seats limited to 75 participants."
            ),
            campus="IU South Bend",
            event_url="https://www.iusb.edu/community-engagement/index.html",
            check_in_code="SBCEF25",
            points=10,
            event_date=now + timedelta(days=16, hours=13),
        ),
        Event(                                           # index 32 → 25 pts
            title="Southeast Business Pitch Competition",
            category="Career",
            description=(
                "Present your startup idea to a panel of Louisville-area investors and Kelley "
                "faculty judges. Teams of 1-4 have 8 minutes to pitch, then face Q&A. "
                "Winner receives $1,000 and mentorship from IU Ventures."
            ),
            campus="IU Southeast",
            event_url="https://www.ius.edu/business/student-resources.html",
            check_in_code="SEBPC25",
            points=25,
            event_date=now + timedelta(days=17, hours=14),
        ),
        Event(                                           # index 33 → 30 pts
            title="Columbus Nursing Clinical Showcase",
            category="Academic",
            description=(
                "IU Columbus nursing students present their capstone clinical projects to "
                "Bartholomew County health professionals. Topics include elder care, "
                "community health, and pediatric nursing innovations."
            ),
            campus="IU Columbus",
            event_url="https://columbus.iu.edu/academics/nursing.html",
            check_in_code="COLNRS5",
            points=30,
            event_date=now + timedelta(days=18, hours=10),
        ),
        Event(                                           # index 34 → 15 pts
            title="Fort Wayne Engineering Career Night",
            category="Career",
            description=(
                "Network with engineers from Raytheon, Lincoln Financial, Steel Dynamics, and "
                "other Fort Wayne employers. Dress business casual, bring 10 copies of your "
                "resume, and explore full-time and co-op opportunities."
            ),
            campus="IU Fort Wayne",
            event_url="https://www.iufw.edu/engineering-technology/index.html",
            check_in_code="FWECN25",
            points=15,
            event_date=now + timedelta(days=19, hours=17),
        ),
        Event(                                           # index 35 → 40 pts
            title="IU Mental Health Awareness Walk",
            category="Health",
            description=(
                "Join IU's Counseling and Psychological Services for a 2-mile mindfulness walk "
                "through campus. Ends with guided meditation, resource tables, and free "
                "therapy pet visits. Together we walk to reduce stigma around mental health."
            ),
            campus="IU Bloomington",
            event_url="https://healthcenter.indiana.edu/counseling/index.html",
            check_in_code="MHWALK5",
            points=40,
            event_date=now + timedelta(days=20, hours=8),
        ),
        Event(                                           # index 36 → 20 pts
            title="Open Source Contribution Day",
            category="Tech",
            description=(
                "Collaborate on real open-source projects alongside IU Computer Science faculty "
                "and industry mentors. Beginners welcome — learn Git, GitHub workflows, and "
                "how to make your first pull request to a production codebase."
            ),
            campus="IU Bloomington",
            event_url="https://luddy.indiana.edu/research/centers/index.html",
            check_in_code="OPENSR5",
            points=20,
            event_date=now + timedelta(days=21, hours=10),
        ),
        Event(                                           # index 37 → 35 pts
            title="IU vs Purdue Rivalry Tailgate",
            category="Sports",
            description=(
                "The biggest rivalry in Indiana college sports. Join thousands of Hoosier fans "
                "for the pre-game tailgate outside Memorial Stadium. Live DJ, food trucks, "
                "face painting, and Hoosier swag giveaways. Go IU!"
            ),
            campus="IU Bloomington",
            event_url="https://iuhoosiers.com/sports/football",
            check_in_code="RIVTAL5",
            points=35,
            event_date=now + timedelta(days=22, hours=12),
        ),
        Event(                                           # index 38 → 5 pts
            title="AI Ethics Panel Discussion",
            category="Tech",
            description=(
                "Explore the ethical dimensions of artificial intelligence with Luddy School "
                "professors, a tech industry ethicist, and a policy researcher. Topics: bias "
                "in algorithms, AI in healthcare, surveillance, and responsible innovation."
            ),
            campus="IU Bloomington",
            event_url="https://luddy.indiana.edu/news-events/events/index.html",
            check_in_code="AIETHIC5",
            points=5,
            event_date=now + timedelta(days=23, hours=14),
        ),
        Event(                                           # index 39 → 45 pts
            title="Asian Pacific Heritage Showcase",
            category="Cultural",
            description=(
                "Celebrate Asian and Pacific Islander cultures through traditional dance "
                "performances, art displays, cuisine tastings, and a spoken word showcase. "
                "Organized by IUPUI's Asian Cultural Center — all are welcome."
            ),
            campus="IU Indianapolis",
            event_url="https://diversity.iupui.edu/centers/asian/events.html",
            check_in_code="APHA2025",
            points=45,
            event_date=now + timedelta(days=24, hours=16),
        ),
        Event(                                           # index 40 → 50 pts
            title="Free Flu Shot & Health Screening",
            category="Health",
            description=(
                "IU Health Services is offering free flu vaccinations, blood pressure checks, "
                "glucose screening, and BMI assessments. No appointment needed — walk in with "
                "your IU ID. Protect yourself and your campus community."
            ),
            campus="IU Bloomington",
            event_url="https://healthcenter.indiana.edu/index.html",
            check_in_code="FLUSHOOT",
            points=50,
            event_date=now + timedelta(days=25, hours=9),
        ),
        Event(                                           # index 41 → 10 pts
            title="Greek Life Philanthropy Fair",
            category="Social",
            description=(
                "IU fraternities and sororities showcase their annual philanthropy projects "
                "and community service initiatives. Learn how to get involved, meet chapter "
                "members, and discover volunteer opportunities across Bloomington."
            ),
            campus="IU Bloomington",
            event_url="https://studentlife.indiana.edu/social-opportunities/greek-life/index.html",
            check_in_code="GREEKPH5",
            points=10,
            event_date=now + timedelta(days=26, hours=11),
        ),
        Event(                                           # index 42 → 25 pts
            title="Resume & LinkedIn Workshop",
            category="Career",
            description=(
                "Career coaches from IU Indianapolis Career Services will review your resume "
                "live and help optimize your LinkedIn profile for recruiter visibility. "
                "Bring your laptop and a printed copy of your current resume."
            ),
            campus="IU Indianapolis",
            event_url="https://career.iupui.edu/channels/events/index.html",
            check_in_code="RESLINK5",
            points=25,
            event_date=now + timedelta(days=27, hours=13),
        ),
        Event(                                           # index 43 → 30 pts
            title="IU Sustainability Earth Week",
            category="Social",
            description=(
                "A week-long series of events including a campus sustainability tour, zero-waste "
                "cooking demo, solar energy workshop, and documentary screening of 'Kiss the "
                "Ground'. Hosted by IU's Office of Sustainability."
            ),
            campus="IU Bloomington",
            event_url="https://sustain.indiana.edu/programs/earth-week.html",
            check_in_code="EARTHWK5",
            points=30,
            event_date=now + timedelta(days=28, hours=10),
        ),
        Event(                                           # index 44 → 15 pts
            title="International Student Welcome Mixer",
            category="Cultural",
            description=(
                "A warm welcome for IU's 5,000+ international students from 150+ countries. "
                "Meet peers from around the globe, explore campus resources, and enjoy "
                "international food and cultural performances at the IMU Grand Hall."
            ),
            campus="IU Bloomington",
            event_url="https://ois.iu.edu/living-in-bloomington/events.html",
            check_in_code="INTLMIX5",
            points=15,
            event_date=now + timedelta(days=29, hours=18),
        ),
        Event(                                           # index 45 → 40 pts
            title="Midnight Run Charity 5K",
            category="Sports",
            description=(
                "Lace up and run through a lit campus course starting at midnight. All proceeds "
                "benefit the IU Food Pantry. Costumes encouraged! Timed chip race with prizes "
                "for top 3 finishers in each age category. Registration $15 at the door."
            ),
            campus="IU Bloomington",
            event_url="https://recsports.indiana.edu/events/index.html",
            check_in_code="MIDRUN25",
            points=40,
            event_date=now + timedelta(days=30, hours=0),
        ),
        Event(                                           # index 46 → 20 pts
            title="App Development Bootcamp",
            category="Tech",
            description=(
                "A two-day intensive bootcamp where students build and deploy a mobile app "
                "from scratch using React Native. Mentored by IU Southeast CS faculty and "
                "Louisville-based software engineers. No prior mobile experience required."
            ),
            campus="IU Southeast",
            event_url="https://www.ius.edu/informatics/index.html",
            check_in_code="APPBOOT5",
            points=20,
            event_date=now + timedelta(days=30, hours=9),
        ),
    ]
    db.add_all(events)
    db.flush()

    # ── Students (25 realistic IU students across all campuses) ───────────────
    students = [
        # IU Bloomington (8)
        Student(name="Aiden Ramirez",     iu_username="aramirez",  campus="IU Bloomington",
                major="Computer Science", year="Junior"),
        Student(name="Sofia Chen",         iu_username="schen",     campus="IU Bloomington",
                major="Informatics", year="Senior"),
        Student(name="Marcus Williams",    iu_username="mwilliams", campus="IU Bloomington",
                major="Business", year="Junior"),
        Student(name="Priya Patel",        iu_username="ppatel",    campus="IU Bloomington",
                major="Mathematics", year="Sophomore"),
        Student(name="Ethan Kowalski",     iu_username="ekowalski", campus="IU Bloomington",
                major="Computer Science", year="Senior"),
        Student(name="Olivia Thompson",    iu_username="othompson", campus="IU Bloomington",
                major="Psychology", year="Freshman"),
        Student(name="James Okonkwo",      iu_username="jokonkwo",  campus="IU Bloomington",
                major="Informatics", year="Graduate"),
        Student(name="Emma Nguyen",        iu_username="enguyen",   campus="IU Bloomington",
                major="Biology", year="Junior"),
        # IU Indianapolis (5)
        Student(name="Carlos Rivera",      iu_username="crivera",   campus="IU Indianapolis",
                major="Nursing", year="Senior"),
        Student(name="Fatima Al-Rashid",   iu_username="falrashid", campus="IU Indianapolis",
                major="Computer Science", year="Sophomore"),
        Student(name="Tyler Brooks",       iu_username="tbrooks",   campus="IU Indianapolis",
                major="Business", year="Junior"),
        Student(name="Amara Osei",         iu_username="aosei",     campus="IU Indianapolis",
                major="Public Health", year="Graduate"),
        Student(name="Liam Fitzgerald",    iu_username="lfitzgerald", campus="IU Indianapolis",
                major="Biology", year="Sophomore"),
        # IU East (2)
        Student(name="Hannah Kim",         iu_username="hkim",      campus="IU East",
                major="Psychology", year="Junior"),
        Student(name="Noah Patterson",     iu_username="npatterson", campus="IU East",
                major="Computer Science", year="Freshman"),
        # IU Kokomo (2)
        Student(name="Zoe Hernandez",      iu_username="zhernandez", campus="IU Kokomo",
                major="Business", year="Senior"),
        Student(name="Ben Okafor",         iu_username="bokafor",   campus="IU Kokomo",
                major="Mathematics", year="Junior"),
        # IU Northwest (2)
        Student(name="Layla Singh",        iu_username="lsingh",    campus="IU Northwest",
                major="Informatics", year="Graduate"),
        Student(name="Diego Morales",      iu_username="dmorales",  campus="IU Northwest",
                major="Social Work", year="Senior"),
        # IU South Bend (2)
        Student(name="Chloe Baker",        iu_username="cbaker",    campus="IU South Bend",
                major="Education", year="Junior"),
        Student(name="Lucas Johansson",    iu_username="ljohansson", campus="IU South Bend",
                major="Business", year="Sophomore"),
        # IU Southeast (2)
        Student(name="Mia Foster",         iu_username="mfoster",   campus="IU Southeast",
                major="Computer Science", year="Senior"),
        Student(name="Elijah Washington",  iu_username="ewashington", campus="IU Southeast",
                major="Criminal Justice", year="Junior"),
        # IU Columbus (1)
        Student(name="Ava Martinez",       iu_username="amartinez", campus="IU Columbus",
                major="Nursing", year="Sophomore"),
        # IU Fort Wayne (1)
        Student(name="Jack Schneider",     iu_username="jschneider", campus="IU Fort Wayne",
                major="Engineering", year="Graduate"),
    ]
    db.add_all(students)
    db.flush()

    s = students  # alias for brevity
    e = events

    # ── Attendance records (spread across the week, realistic point totals) ───
    # Format: (student_index, event_index, day_offset, hour_offset)
    checkins = [
        # Aiden — top performer: 5 events
        (0, 0, 1, 9),   (0, 5, 3, 9),   (0, 1, 1, 13),  (0, 2, 2, 10),  (0, 3, 2, 14),
        # Sofia — 4 events
        (1, 0, 1, 9),   (1, 5, 3, 9),   (1, 1, 1, 13),  (1, 4, 2, 17),
        # Marcus — 4 events
        (2, 0, 1, 9),   (2, 5, 3, 10),  (2, 6, 3, 12),  (2, 14, 6, 11),
        # Carlos — 3 events
        (8, 2, 2, 10),  (8, 13, 5, 9),  (8, 7, 3, 18),
        # Priya — 3 events
        (3, 0, 1, 9),   (3, 1, 1, 14),  (3, 3, 2, 14),
        # Fatima — 3 events
        (9, 2, 2, 10),  (9, 13, 5, 9),  (9, 8, 4, 11),
        # Ethan — 3 events
        (4, 5, 3, 9),   (4, 3, 2, 15),  (4, 14, 6, 11),
        # Olivia — 3 events
        (5, 0, 1, 10),  (5, 12, 5, 14), (5, 14, 6, 12),
        # Layla — 2 events
        (17, 8, 4, 11), (17, 11, 5, 10),
        # Tyler — 2 events
        (10, 2, 2, 10), (10, 13, 5, 10),
        # James — 2 events
        (6, 5, 3, 9),   (6, 6, 3, 12),
        # Hannah — 2 events
        (13, 4, 2, 17), (13, 9, 4, 9),
        # Diego — 2 events
        (18, 8, 4, 11), (18, 6, 3, 13),
        # Amara — 2 events
        (11, 13, 5, 9), (11, 2, 2, 11),
        # Emma — 2 events
        (7, 0, 1, 10),  (7, 12, 5, 14),
        # Noah — 2 events
        (14, 4, 2, 17), (14, 9, 4, 9),
        # Liam — 2 events
        (12, 13, 5, 9), (12, 8, 4, 12),
        # Zoe — 1 event
        (15, 7, 3, 18),
        # Ben — 1 event
        (16, 7, 3, 19),
        # Chloe — 1 event
        (19, 6, 3, 12),
        # Lucas — 1 event
        (20, 6, 3, 13),
        # Mia — 1 event
        (21, 9, 4, 9),
        # Elijah — 1 event
        (22, 9, 4, 10),
        # Ava — 1 event
        (23, 10, 4, 13),
        # Jack — 1 event
        (24, 11, 5, 10),
    ]

    records = []
    seen = set()
    for (si, ei, day, hour) in checkins:
        key = (si, ei)
        if key in seen:
            continue
        seen.add(key)
        records.append(Attendance(
            student_id=s[si].id,
            event_id=e[ei].id,
            points_earned=e[ei].points,
            checked_in_at=week_start + timedelta(days=day, hours=hour, minutes=(si * 3 + ei) % 45),
        ))

    db.add_all(records)

    # ── Seed event_codes table ────────────────────────────────────────────────
    for ev in events:
        db.add(EventCode(
            event_id=ev.id,
            event_name=ev.title,
            code=ev.check_in_code,
            set_by="system",
            updated_at=utcnow(),
        ))

    db.commit()
    print(
        "[EngageIU] Seeded {} events, {} students, {} attendance records.".format(
            len(events), len(students), len(records)
        )
    )

if __name__ == "__main__":
    from database import SessionLocal
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
