# coding=utf-8

from subliminal.providers.shooter import ShooterProvider as _ShooterProvider, ShooterSubtitle as _ShooterSubtitle


class ShooterSubtitle(_ShooterSubtitle):
    pass


class ShooterProvider(_ShooterProvider):
    subtitle_class = ShooterSubtitle