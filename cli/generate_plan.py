"""Generate daily training plan."""
from src.training.plan_generator import PlanGenerator


def main():
    print("\n♟️  Daily Training Plan Generator")
    print("=" * 60)
    
    generator = PlanGenerator()
    generator.generate_plan()
    generator.close()


if __name__ == "__main__":
    main()
