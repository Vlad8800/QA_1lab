"""Lab 8 baseline: an intentionally brittle three-level shipping rule hierarchy."""

from app.services import ShippingOrderSpec


class BaseShippingQuote:
    """Shared quote policy at depth 1."""

    def validate(self, spec: ShippingOrderSpec, base_rate: float) -> None:
        if base_rate < 0:
            raise ValueError("Base rate must be non-negative")

    def supports(self, spec: ShippingOrderSpec) -> bool:
        return True

    def quote(self, spec: ShippingOrderSpec, base_rate: float, *, policy_context: str) -> float:
        if not policy_context:
            raise ValueError("Policy context is required")
        self.validate(spec, base_rate)
        return spec.calculate_cost(base_rate)

    def mode(self, spec: ShippingOrderSpec, is_fallback: bool) -> str:
        return spec.resolve_mode(is_fallback)


class RegionalShippingQuote(BaseShippingQuote):
    """Regional specialization: two of four inherited operations are overridden."""

    def supports(self, spec: ShippingOrderSpec) -> bool:
        return spec.country == "UA" or super().supports(spec)

    def quote(self, spec: ShippingOrderSpec, base_rate: float) -> float:
        self.validate(spec, base_rate)
        if spec.country == "UA":
            return round(base_rate, 2)
        return super().quote(spec, base_rate)


class ExpressHolidayShippingQuote(RegionalShippingQuote):
    """Deep specialization: another two inherited operations are overridden."""

    def quote(self, spec: ShippingOrderSpec, base_rate: float) -> float:
        amount = super().quote(spec, base_rate)
        if spec.is_express and spec.is_holiday and spec.customer_tier == "vip":
            return round(amount * 0.95, 2)
        return amount

    def mode(self, spec: ShippingOrderSpec, is_fallback: bool) -> str:
        inherited_mode = super().mode(spec, is_fallback)
        if spec.is_express and spec.is_holiday:
            return f"express_holiday:{inherited_mode}"
        return inherited_mode
