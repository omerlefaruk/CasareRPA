"""
Business Calendar for CasareRPA Orchestrator.

Handles business hours, holidays, blackout periods, and timezone-aware scheduling.
Provides validation for enterprise scheduling constraints.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from zoneinfo import ZoneInfo
import threading
import calendar

from loguru import logger


class DayOfWeek(Enum):
    """Days of the week."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    @classmethod
    def from_date(cls, d: date) -> "DayOfWeek":
        """Get day of week from date."""
        return cls(d.weekday())


class HolidayType(Enum):
    """Types of holidays for scheduling behavior."""

    FIXED = "fixed"  # Same date every year (e.g., Jan 1)
    FLOATING = "floating"  # Nth weekday of month (e.g., Thanksgiving)
    CUSTOM = "custom"  # Manually specified dates


@dataclass
class Holiday:
    """
    Represents a holiday or non-working day.

    Attributes:
        name: Human-readable holiday name
        holiday_type: Type of holiday for recurrence calculation
        month: Month number (1-12)
        day: Day of month for fixed holidays, or None for floating
        weekday: Day of week for floating holidays
        occurrence: Which occurrence for floating (1st, 2nd, -1 for last, etc.)
        year: Specific year (None for recurring annually)
        observance: Whether to observe on nearest weekday if falls on weekend
    """

    name: str
    holiday_type: HolidayType
    month: int
    day: Optional[int] = None
    weekday: Optional[DayOfWeek] = None
    occurrence: Optional[int] = None
    year: Optional[int] = None
    observance: bool = False

    def get_date(self, year: int) -> Optional[date]:
        """
        Calculate the actual date of this holiday for a given year.

        Args:
            year: Year to calculate for

        Returns:
            Date of holiday or None if not applicable
        """
        if self.year is not None and self.year != year:
            return None

        if self.holiday_type == HolidayType.FIXED:
            if self.day is None:
                return None
            try:
                holiday_date = date(year, self.month, self.day)
            except ValueError:
                return None
        elif self.holiday_type == HolidayType.FLOATING:
            if self.weekday is None or self.occurrence is None:
                return None
            holiday_date = self._calculate_floating_date(year)
            if holiday_date is None:
                return None
        else:
            if self.day is None:
                return None
            try:
                holiday_date = date(year, self.month, self.day)
            except ValueError:
                return None

        if self.observance:
            holiday_date = self._apply_observance(holiday_date)

        return holiday_date

    def _calculate_floating_date(self, year: int) -> Optional[date]:
        """Calculate date for floating holidays (Nth weekday of month)."""
        if self.weekday is None or self.occurrence is None:
            return None

        target_weekday = self.weekday.value
        cal = calendar.Calendar()
        month_days = list(cal.itermonthdays2(year, self.month))

        matching_days = [
            day for day, weekday in month_days if day != 0 and weekday == target_weekday
        ]

        if not matching_days:
            return None

        if self.occurrence > 0:
            idx = self.occurrence - 1
            if idx >= len(matching_days):
                return None
            return date(year, self.month, matching_days[idx])
        else:
            idx = self.occurrence
            if abs(idx) > len(matching_days):
                return None
            return date(year, self.month, matching_days[idx])

    def _apply_observance(self, d: date) -> date:
        """Move weekend holidays to nearest weekday."""
        if d.weekday() == 5:
            return d - timedelta(days=1)
        elif d.weekday() == 6:
            return d + timedelta(days=1)
        return d


@dataclass
class WorkingHours:
    """
    Represents working hours for a day.

    Attributes:
        start: Start time
        end: End time
        enabled: Whether work is allowed on this day
    """

    start: time = field(default_factory=lambda: time(9, 0))
    end: time = field(default_factory=lambda: time(17, 0))
    enabled: bool = True

    def contains(self, t: time) -> bool:
        """Check if time falls within working hours."""
        if not self.enabled:
            return False
        return self.start <= t <= self.end

    def minutes_remaining(self, from_time: time) -> int:
        """Calculate minutes remaining in working hours from given time."""
        if not self.enabled or from_time >= self.end:
            return 0
        if from_time < self.start:
            from_time = self.start
        end_minutes = self.end.hour * 60 + self.end.minute
        from_minutes = from_time.hour * 60 + from_time.minute
        return max(0, end_minutes - from_minutes)


@dataclass
class BlackoutPeriod:
    """
    Represents a period when scheduling is blocked.

    Attributes:
        name: Human-readable name for the blackout
        start: Start datetime (timezone-aware)
        end: End datetime (timezone-aware)
        reason: Explanation for the blackout
        recurring: Whether this recurs annually
        affects_workflows: List of workflow IDs affected (empty = all)
    """

    name: str
    start: datetime
    end: datetime
    reason: str = ""
    recurring: bool = False
    affects_workflows: List[str] = field(default_factory=list)

    def is_active(
        self, check_time: datetime, workflow_id: Optional[str] = None
    ) -> bool:
        """
        Check if blackout is active at given time.

        Args:
            check_time: Time to check
            workflow_id: Optional workflow ID for filtering

        Returns:
            True if blackout is active
        """
        if self.affects_workflows and workflow_id:
            if workflow_id not in self.affects_workflows:
                return False

        if self.recurring:
            check_year = check_time.year
            start_adjusted = self.start.replace(year=check_year)
            end_adjusted = self.end.replace(year=check_year)
            if start_adjusted > end_adjusted:
                return check_time >= start_adjusted or check_time <= end_adjusted
            return start_adjusted <= check_time <= end_adjusted

        return self.start <= check_time <= self.end

    def overlaps(self, start: datetime, end: datetime) -> bool:
        """Check if period overlaps with given range."""
        return self.start < end and self.end > start


@dataclass
class CalendarConfig:
    """
    Configuration for a business calendar.

    Attributes:
        timezone: Default timezone for the calendar
        working_hours: Working hours per day of week
        holidays: List of holidays
        blackouts: List of blackout periods
        allow_weekends: Whether to allow execution on weekends
        allow_outside_hours: Whether to allow execution outside working hours
    """

    timezone: str = "UTC"
    working_hours: Dict[DayOfWeek, WorkingHours] = field(default_factory=dict)
    holidays: List[Holiday] = field(default_factory=list)
    blackouts: List[BlackoutPeriod] = field(default_factory=list)
    allow_weekends: bool = False
    allow_outside_hours: bool = False

    def __post_init__(self):
        """Initialize default working hours if not provided."""
        if not self.working_hours:
            self.working_hours = {
                DayOfWeek.MONDAY: WorkingHours(),
                DayOfWeek.TUESDAY: WorkingHours(),
                DayOfWeek.WEDNESDAY: WorkingHours(),
                DayOfWeek.THURSDAY: WorkingHours(),
                DayOfWeek.FRIDAY: WorkingHours(),
                DayOfWeek.SATURDAY: WorkingHours(enabled=False),
                DayOfWeek.SUNDAY: WorkingHours(enabled=False),
            }


class BusinessCalendar:
    """
    Business calendar for enterprise scheduling.

    Features:
    - Holiday management with fixed and floating holidays
    - Working hours configuration per day
    - Blackout period management
    - Timezone-aware scheduling validation
    - Next working time calculation
    """

    US_FEDERAL_HOLIDAYS: List[Holiday] = [
        Holiday("New Year's Day", HolidayType.FIXED, 1, 1, observance=True),
        Holiday(
            "Martin Luther King Jr. Day",
            HolidayType.FLOATING,
            1,
            weekday=DayOfWeek.MONDAY,
            occurrence=3,
        ),
        Holiday(
            "Presidents' Day",
            HolidayType.FLOATING,
            2,
            weekday=DayOfWeek.MONDAY,
            occurrence=3,
        ),
        Holiday(
            "Memorial Day",
            HolidayType.FLOATING,
            5,
            weekday=DayOfWeek.MONDAY,
            occurrence=-1,
        ),
        Holiday("Independence Day", HolidayType.FIXED, 7, 4, observance=True),
        Holiday(
            "Labor Day",
            HolidayType.FLOATING,
            9,
            weekday=DayOfWeek.MONDAY,
            occurrence=1,
        ),
        Holiday(
            "Columbus Day",
            HolidayType.FLOATING,
            10,
            weekday=DayOfWeek.MONDAY,
            occurrence=2,
        ),
        Holiday("Veterans Day", HolidayType.FIXED, 11, 11, observance=True),
        Holiday(
            "Thanksgiving",
            HolidayType.FLOATING,
            11,
            weekday=DayOfWeek.THURSDAY,
            occurrence=4,
        ),
        Holiday("Christmas Day", HolidayType.FIXED, 12, 25, observance=True),
    ]

    UK_BANK_HOLIDAYS: List[Holiday] = [
        Holiday("New Year's Day", HolidayType.FIXED, 1, 1, observance=True),
        Holiday(
            "Early May Bank Holiday",
            HolidayType.FLOATING,
            5,
            weekday=DayOfWeek.MONDAY,
            occurrence=1,
        ),
        Holiday(
            "Spring Bank Holiday",
            HolidayType.FLOATING,
            5,
            weekday=DayOfWeek.MONDAY,
            occurrence=-1,
        ),
        Holiday(
            "Summer Bank Holiday",
            HolidayType.FLOATING,
            8,
            weekday=DayOfWeek.MONDAY,
            occurrence=-1,
        ),
        Holiday("Christmas Day", HolidayType.FIXED, 12, 25, observance=True),
        Holiday("Boxing Day", HolidayType.FIXED, 12, 26, observance=True),
    ]

    def __init__(self, config: Optional[CalendarConfig] = None):
        """
        Initialize business calendar.

        Args:
            config: Calendar configuration (uses defaults if not provided)
        """
        self._config = config or CalendarConfig()
        self._tz = ZoneInfo(self._config.timezone)
        self._holiday_cache: Dict[int, Set[date]] = {}
        self._cache_lock = threading.Lock()
        self._custom_dates: Set[date] = set()

        logger.info(
            f"BusinessCalendar initialized with timezone: {self._config.timezone}"
        )

    @property
    def timezone(self) -> str:
        """Get calendar timezone."""
        return self._config.timezone

    @property
    def config(self) -> CalendarConfig:
        """Get calendar configuration."""
        return self._config

    def add_holiday(self, holiday: Holiday) -> None:
        """
        Add a holiday to the calendar.

        Args:
            holiday: Holiday to add
        """
        self._config.holidays.append(holiday)
        with self._cache_lock:
            self._holiday_cache.clear()
        logger.debug(f"Added holiday: {holiday.name}")

    def remove_holiday(self, name: str) -> bool:
        """
        Remove a holiday by name.

        Args:
            name: Holiday name

        Returns:
            True if holiday was removed
        """
        original_count = len(self._config.holidays)
        self._config.holidays = [h for h in self._config.holidays if h.name != name]
        if len(self._config.holidays) < original_count:
            with self._cache_lock:
                self._holiday_cache.clear()
            logger.debug(f"Removed holiday: {name}")
            return True
        return False

    def add_blackout(self, blackout: BlackoutPeriod) -> None:
        """
        Add a blackout period.

        Args:
            blackout: Blackout period to add
        """
        self._config.blackouts.append(blackout)
        logger.debug(
            f"Added blackout: {blackout.name} ({blackout.start} - {blackout.end})"
        )

    def remove_blackout(self, name: str) -> bool:
        """
        Remove a blackout period by name.

        Args:
            name: Blackout name

        Returns:
            True if blackout was removed
        """
        original_count = len(self._config.blackouts)
        self._config.blackouts = [b for b in self._config.blackouts if b.name != name]
        if len(self._config.blackouts) < original_count:
            logger.debug(f"Removed blackout: {name}")
            return True
        return False

    def add_custom_date(self, d: date) -> None:
        """Add a custom non-working date."""
        self._custom_dates.add(d)

    def remove_custom_date(self, d: date) -> bool:
        """Remove a custom non-working date."""
        if d in self._custom_dates:
            self._custom_dates.discard(d)
            return True
        return False

    def set_working_hours(self, day: DayOfWeek, hours: WorkingHours) -> None:
        """
        Set working hours for a specific day.

        Args:
            day: Day of week
            hours: Working hours configuration
        """
        self._config.working_hours[day] = hours
        logger.debug(
            f"Set working hours for {day.name}: {hours.start} - {hours.end} "
            f"(enabled={hours.enabled})"
        )

    def get_holidays_for_year(self, year: int) -> List[Tuple[date, str]]:
        """
        Get all holidays for a year.

        Args:
            year: Year to get holidays for

        Returns:
            List of (date, name) tuples
        """
        holidays = []
        for holiday in self._config.holidays:
            holiday_date = holiday.get_date(year)
            if holiday_date:
                holidays.append((holiday_date, holiday.name))
        holidays.sort(key=lambda x: x[0])
        return holidays

    def _get_holiday_dates(self, year: int) -> Set[date]:
        """Get cached set of holiday dates for a year."""
        with self._cache_lock:
            if year not in self._holiday_cache:
                dates = set()
                for holiday in self._config.holidays:
                    holiday_date = holiday.get_date(year)
                    if holiday_date:
                        dates.add(holiday_date)
                self._holiday_cache[year] = dates
            return self._holiday_cache[year]

    def is_holiday(self, d: date) -> bool:
        """
        Check if a date is a holiday.

        Args:
            d: Date to check

        Returns:
            True if date is a holiday
        """
        return d in self._get_holiday_dates(d.year)

    def is_custom_non_working(self, d: date) -> bool:
        """Check if date is a custom non-working date."""
        return d in self._custom_dates

    def is_weekend(self, d: date) -> bool:
        """
        Check if a date falls on a weekend.

        Args:
            d: Date to check

        Returns:
            True if Saturday or Sunday
        """
        return d.weekday() >= 5

    def is_working_day(self, d: date) -> bool:
        """
        Check if a date is a working day.

        Args:
            d: Date to check

        Returns:
            True if date is a working day
        """
        if self.is_holiday(d):
            return False
        if self.is_custom_non_working(d):
            return False
        if self.is_weekend(d) and not self._config.allow_weekends:
            return False

        day_of_week = DayOfWeek.from_date(d)
        hours = self._config.working_hours.get(day_of_week)
        if hours and not hours.enabled:
            return False

        return True

    def is_within_working_hours(self, dt: datetime) -> bool:
        """
        Check if datetime is within working hours.

        Args:
            dt: Datetime to check (timezone-aware or naive)

        Returns:
            True if within working hours
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self._tz)
        else:
            dt = dt.astimezone(self._tz)

        if not self.is_working_day(dt.date()):
            return False

        if self._config.allow_outside_hours:
            return True

        day_of_week = DayOfWeek.from_date(dt.date())
        hours = self._config.working_hours.get(day_of_week)
        if hours is None:
            return True

        return hours.contains(dt.time())

    def is_in_blackout(
        self, dt: datetime, workflow_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if datetime is in a blackout period.

        Args:
            dt: Datetime to check
            workflow_id: Optional workflow ID for filtering

        Returns:
            Tuple of (is_blocked, blackout_reason)
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self._tz)

        for blackout in self._config.blackouts:
            if blackout.is_active(dt, workflow_id):
                return True, blackout.reason or blackout.name

        return False, None

    def can_execute(
        self,
        dt: datetime,
        workflow_id: Optional[str] = None,
        ignore_hours: bool = False,
        ignore_blackouts: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if execution is allowed at given time.

        Args:
            dt: Datetime to check
            workflow_id: Optional workflow ID for blackout filtering
            ignore_hours: Ignore working hours restriction
            ignore_blackouts: Ignore blackout periods

        Returns:
            Tuple of (can_execute, reason_if_blocked)
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self._tz)

        if not ignore_blackouts:
            in_blackout, reason = self.is_in_blackout(dt, workflow_id)
            if in_blackout:
                return False, f"Blackout: {reason}"

        if self.is_holiday(dt.date()):
            return False, f"Holiday: {dt.date()}"

        if self.is_custom_non_working(dt.date()):
            return False, f"Non-working date: {dt.date()}"

        if self.is_weekend(dt.date()) and not self._config.allow_weekends:
            return False, "Weekend execution not allowed"

        if not ignore_hours and not self._config.allow_outside_hours:
            if not self.is_within_working_hours(dt):
                return False, "Outside working hours"

        return True, None

    def get_next_working_time(
        self,
        from_time: Optional[datetime] = None,
        workflow_id: Optional[str] = None,
        max_days_ahead: int = 30,
    ) -> Optional[datetime]:
        """
        Get the next valid working time.

        Args:
            from_time: Starting time (default: now)
            workflow_id: Optional workflow ID for blackout filtering
            max_days_ahead: Maximum days to search ahead

        Returns:
            Next valid working datetime or None if not found
        """
        if from_time is None:
            from_time = datetime.now(self._tz)
        elif from_time.tzinfo is None:
            from_time = from_time.replace(tzinfo=self._tz)
        else:
            from_time = from_time.astimezone(self._tz)

        current = from_time
        end_search = from_time + timedelta(days=max_days_ahead)

        while current < end_search:
            can_exec, _ = self.can_execute(current, workflow_id)
            if can_exec:
                return current

            day_of_week = DayOfWeek.from_date(current.date())
            hours = self._config.working_hours.get(day_of_week)

            if hours and hours.enabled:
                if current.time() < hours.start:
                    next_start = datetime.combine(current.date(), hours.start)
                    next_start = next_start.replace(tzinfo=self._tz)
                    can_exec, _ = self.can_execute(next_start, workflow_id)
                    if can_exec:
                        return next_start

            tomorrow = current.date() + timedelta(days=1)
            next_day = DayOfWeek.from_date(tomorrow)
            next_hours = self._config.working_hours.get(next_day)
            if next_hours and next_hours.enabled:
                current = datetime.combine(tomorrow, next_hours.start)
            else:
                current = datetime.combine(tomorrow, time(0, 0))
            current = current.replace(tzinfo=self._tz)

        return None

    def adjust_to_working_time(
        self,
        dt: datetime,
        workflow_id: Optional[str] = None,
    ) -> datetime:
        """
        Adjust a datetime to the next valid working time if needed.

        Args:
            dt: Datetime to adjust
            workflow_id: Optional workflow ID for blackout filtering

        Returns:
            Original time if valid, or next working time
        """
        can_exec, _ = self.can_execute(dt, workflow_id)
        if can_exec:
            return dt

        next_time = self.get_next_working_time(dt, workflow_id)
        if next_time:
            return next_time

        return dt

    def count_working_days(self, start: date, end: date) -> int:
        """
        Count working days between two dates (inclusive).

        Args:
            start: Start date
            end: End date

        Returns:
            Number of working days
        """
        if start > end:
            start, end = end, start

        count = 0
        current = start
        while current <= end:
            if self.is_working_day(current):
                count += 1
            current += timedelta(days=1)
        return count

    def add_working_days(self, start: date, days: int) -> date:
        """
        Add working days to a date.

        Args:
            start: Starting date
            days: Number of working days to add

        Returns:
            Result date
        """
        if days == 0:
            return start

        direction = 1 if days > 0 else -1
        remaining = abs(days)
        current = start

        while remaining > 0:
            current += timedelta(days=direction)
            if self.is_working_day(current):
                remaining -= 1

        return current

    def get_working_hours_remaining(self, dt: datetime) -> int:
        """
        Get working minutes remaining in the day.

        Args:
            dt: Current datetime

        Returns:
            Minutes of working time remaining
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self._tz)
        else:
            dt = dt.astimezone(self._tz)

        if not self.is_working_day(dt.date()):
            return 0

        day_of_week = DayOfWeek.from_date(dt.date())
        hours = self._config.working_hours.get(day_of_week)
        if hours is None:
            return 0

        return hours.minutes_remaining(dt.time())

    @classmethod
    def create_us_calendar(
        cls,
        timezone: str = "America/New_York",
        include_federal_holidays: bool = True,
    ) -> "BusinessCalendar":
        """
        Create a calendar configured for US business hours.

        Args:
            timezone: US timezone
            include_federal_holidays: Whether to include federal holidays

        Returns:
            Configured BusinessCalendar
        """
        config = CalendarConfig(timezone=timezone)
        if include_federal_holidays:
            config.holidays = list(cls.US_FEDERAL_HOLIDAYS)

        return cls(config)

    @classmethod
    def create_uk_calendar(
        cls,
        timezone: str = "Europe/London",
        include_bank_holidays: bool = True,
    ) -> "BusinessCalendar":
        """
        Create a calendar configured for UK business hours.

        Args:
            timezone: UK timezone
            include_bank_holidays: Whether to include bank holidays

        Returns:
            Configured BusinessCalendar
        """
        config = CalendarConfig(timezone=timezone)
        if include_bank_holidays:
            config.holidays = list(cls.UK_BANK_HOLIDAYS)

        return cls(config)

    @classmethod
    def create_24_7_calendar(
        cls,
        timezone: str = "UTC",
        holidays: Optional[List[Holiday]] = None,
    ) -> "BusinessCalendar":
        """
        Create a 24/7 calendar with no working hour restrictions.

        Args:
            timezone: Calendar timezone
            holidays: Optional list of holidays

        Returns:
            Configured BusinessCalendar
        """
        config = CalendarConfig(
            timezone=timezone,
            allow_weekends=True,
            allow_outside_hours=True,
            holidays=holidays or [],
        )
        for day in DayOfWeek:
            config.working_hours[day] = WorkingHours(
                start=time(0, 0), end=time(23, 59), enabled=True
            )

        return cls(config)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize calendar to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "timezone": self._config.timezone,
            "allow_weekends": self._config.allow_weekends,
            "allow_outside_hours": self._config.allow_outside_hours,
            "working_hours": {
                day.name: {
                    "start": hours.start.isoformat(),
                    "end": hours.end.isoformat(),
                    "enabled": hours.enabled,
                }
                for day, hours in self._config.working_hours.items()
            },
            "holidays": [
                {
                    "name": h.name,
                    "type": h.holiday_type.value,
                    "month": h.month,
                    "day": h.day,
                    "weekday": h.weekday.name if h.weekday else None,
                    "occurrence": h.occurrence,
                    "year": h.year,
                    "observance": h.observance,
                }
                for h in self._config.holidays
            ],
            "blackouts": [
                {
                    "name": b.name,
                    "start": b.start.isoformat(),
                    "end": b.end.isoformat(),
                    "reason": b.reason,
                    "recurring": b.recurring,
                    "affects_workflows": b.affects_workflows,
                }
                for b in self._config.blackouts
            ],
            "custom_dates": [d.isoformat() for d in self._custom_dates],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessCalendar":
        """
        Create calendar from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            BusinessCalendar instance
        """
        working_hours = {}
        for day_name, hours_data in data.get("working_hours", {}).items():
            day = DayOfWeek[day_name]
            working_hours[day] = WorkingHours(
                start=time.fromisoformat(hours_data["start"]),
                end=time.fromisoformat(hours_data["end"]),
                enabled=hours_data.get("enabled", True),
            )

        holidays = []
        for h_data in data.get("holidays", []):
            weekday = None
            if h_data.get("weekday"):
                weekday = DayOfWeek[h_data["weekday"]]
            holidays.append(
                Holiday(
                    name=h_data["name"],
                    holiday_type=HolidayType(h_data["type"]),
                    month=h_data["month"],
                    day=h_data.get("day"),
                    weekday=weekday,
                    occurrence=h_data.get("occurrence"),
                    year=h_data.get("year"),
                    observance=h_data.get("observance", False),
                )
            )

        blackouts = []
        for b_data in data.get("blackouts", []):
            blackouts.append(
                BlackoutPeriod(
                    name=b_data["name"],
                    start=datetime.fromisoformat(b_data["start"]),
                    end=datetime.fromisoformat(b_data["end"]),
                    reason=b_data.get("reason", ""),
                    recurring=b_data.get("recurring", False),
                    affects_workflows=b_data.get("affects_workflows", []),
                )
            )

        config = CalendarConfig(
            timezone=data.get("timezone", "UTC"),
            working_hours=working_hours,
            holidays=holidays,
            blackouts=blackouts,
            allow_weekends=data.get("allow_weekends", False),
            allow_outside_hours=data.get("allow_outside_hours", False),
        )

        calendar_instance = cls(config)

        for date_str in data.get("custom_dates", []):
            calendar_instance.add_custom_date(date.fromisoformat(date_str))

        return calendar_instance
